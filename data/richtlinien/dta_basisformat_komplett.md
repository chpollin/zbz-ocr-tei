## Inhaltliche Grobstrukturierung von Dokumenten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/TEIStruktur.html](https://www.deutschestextarchiv.de/doku/basisformat/TEIStruktur.html)

# Inhaltliche Grobstrukturierung von Dokumenten

Für jedes Dokument wird innerhalb des `<text>`-Bereichs eine Grobstrukturierung, bestehend aus drei Bereichen, angebracht: einem
`<front>`-Bereich, der die [Titelei](front.html) enthält, einen `<body>`-Bereich, in welchem der [Textkörper](body.html) steht, und ggf. einem `<back>`-Bereich, in welchem sämtliche [Anhänge](anhang.html) zusammengefasst sind.

Außerhalb dieser Container-Elemente stehen keine weiteren Elemente, d.h. das öffnende `<body>`-Tag folgt direkt auf das
schließende `</front>`-Tag, steht also noch
vor jedem neuen Seitenumbruch. Ebenso folgt das öffnende `<back>`-Tag direkt auf das schließende
`</body>`-Tag, wiederum noch vor jedem neuen Seitenumbruch.

```
<text>
  <front>[...]</front>
  <body>
    <pb/>
    [...]
  </body>
  <back>
    <pb/>
    [...]
  </back>
</text>
```


---

## Grundstruktur der Kodierung von Abbildungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/abbKennzeichnung.html](https://www.deutschestextarchiv.de/doku/basisformat/abbKennzeichnung.html)

# Grundstruktur der Kodierung von Abbildungen

Es gibt diverse Formen von Abbildungen, z.B. den Text illustrierende Abbildungen, Tafeln,
Karten, Notenbeispiele, Graphen, spezielle Sonderzeichen.

Abbildungen können jeweils einen Titel (`<head>`) und nähere
Bilderläuterungen (wiedergegeben als normaler Text in Absätzen: `<p>`)
enthalten:

```
<figure>
  <head>[ggf. Titel der Abbildung]</head>
  <p>[ggf. Erläuterung zur Abbildung im Text]</p>
</figure>
```

Die Elemente `<head>` und `<p>` sind dabei
optional. Steht eine Abbildung ohne Titel oder weitere Erläuterung, wird sie durch ein leeres
`<figure/>`-Element dokumentiert.

## Abbildung mit Titel

![](img/U9c7EFoy2w.png)

```
<figure>
  <head>Fig. 274.</head>
</figure>
```

*Quelle: [Wanderley, Germano: Handbuch der Bauconstruktionslehre.
2. Aufl. Bd. 2. Die Constructionen in Stein. Leipzig, 1878. [Faksimile 279]](http://www.deutschestextarchiv.de/wanderley_bauconstructionslehre02_1878/279)*

## Abbildung mit Titel und Erläuterungen

![](img/YivGAoZFH_.png)

```
<figure>
  <head><hi rendition="#g">Fig</hi>. 13.</head>
  <p><hi rendition="#g">Fig</hi>. 13. <hi rendition="#g">Helm</hi> 
  mit Zimier des Königs<lb/><hi rendition="#g">Jakob I. von Arragonien</hi> 
  (1206—1276).<lb/> Orientalisierend. Armeria Real zu Madrid.</p>
</figure><lb/>
```

*Quelle: [Boeheim, Wendelin: Handbuch der Waffenkunde. Leipzig,
1890. [Faksimile 49]](http://www.deutschestextarchiv.de/boeheim_waffenkunde_1890/49)*

HINWEIS:

Darüber hinaus ist es möglich, eine Abbildung mithilfe des @facs-Attributs gezielt
zu verlinken (Level 3).

```
<figure facs="[URI]">
  <head>[ggf. Titel der Abbildung]</head>
  <p>[ggf. Erläuterung zur Abbildung im Text]</p>
</figure>
```

![](img/drcsjlat.png)

```
<div n="1">
  <figure xml:id="figure-0022.1">
    <figure facs="figure-0022-1.jpg"/>
    <p rendition="#aq">DORICA.</p>
    <p rendition="#i">20 Schuchg l 6. Puncten</p>
    <p rendition="#i">3 Schu: 8 zol gl 6.</p>
    <p rendition="#i">Scala<lb/>
13 Schu: 6 zol</p>
  </figure>
</div>
  		
```

*Quelle: [Sandrart, Joachim von: L’Academia Todesca. della Architectura, Scultura & Pittura: Oder Teutsche Academie der Edlen Bau- Bild- und Mahlerey-Künste. Bd. 1,1. Nürnberg, 1675. [Faksimile 38]](http://www.deutschestextarchiv.de/sandrart_academie0101_1675/38)*


---

## Abbildungen im Textbereich

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/abbTextbereich.html](https://www.deutschestextarchiv.de/doku/basisformat/abbTextbereich.html)

# Abbildungen im Textbereich

Steht eine Abbildung im Textbereich, wobei sie über mehrere Zeilen hinwegreicht, so
wird der Hinweis auf die Abbildung dort gesetzt, wo die Abbildung beginnt. Z.B.:

* Abbildung steht linksbündig: `<figure>` steht vor der ersten Zeile
  des Textbereichs, in welchem die Abbildung steht
* Abbildung steht rechtsbündig: `<figure>` steht im Anschluss an die
  erste Zeile des Textbereichs, in welchem die Abbildung steht


---

## Verschachtelte Abbildungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/abbVerschachtelt.html](https://www.deutschestextarchiv.de/doku/basisformat/abbVerschachtelt.html)

# Verschachtelte Abbildungen

Aus mehreren Teil-Illustrationen bestehende Abbildungen werden durch verschachtelte
`<figure>`-Elemente wiedergegeben.

Im Falle verschachtelter Abbildungen kann es notwendig werden, zugunsten der korrekten
Annotation die konsequent zeilengetreue Transkription aufzugeben.

## Verschachtelte Abbildungen I

![](img/af8H8rtjxS.png)

```
<figure>
  <head>Fig. 201.</head><lb/>
  <figure>
    <head>a</head><lb/>
    <p>konzentrisch</p>
  </figure>
  <figure>
    <head>b</head><lb/>
    <p>exzentrisch</p>
  </figure>
</figure><lb/>
```

*Quelle: [Beck, Ludwig: Die Geschichte des Eisens. Bd. 2: Das
XVI. und XVII. Jahrhundert. Braunschweig, 1895. [Faksimile 950]](http://www.deutschestextarchiv.de/beck_eisen02_1895/950)*

## Verschachtelte Abbildungen II

![](img/yW1EiFTSXP.png)

```
<figure> 
  <head>Fig. 14.</head> 
  <figure> 
    <head>a.</head><lb/> 
    <head><hi rendition="#g">Fig.</hi> 14a.</head> 
    <p><hi rendition="#g">Topfhelm</hi> mit Zimier von einer kleinen Reiterstatuette,<lb/> 
    ausgegraben auf der Insel Texel. Anfang des 14. Jahrhunderts. Samm-<lb/>
    lung J. P. Six in Amsterdam. Nach van der Kellen.</p><lb/>
  </figure> 
  <figure> 
    <head>b.</head><lb/>
    <head><hi rendition="#g">Fig.</hi> 14b.</head> 
    <p>Rückseite.</p><lb/>
  </figure> 
</figure>
```

*Quelle: [Boeheim, Wendelin: Handbuch der Waffenkunde. Leipzig,
1890. [Faksimile 50]](http://www.deutschestextarchiv.de/boeheim_waffenkunde_1890/50)*


---

## Abbildungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/abbildung.html](https://www.deutschestextarchiv.de/doku/basisformat/abbildung.html)

# Abbildungen

## Themen

* [Abbildungen Grundstruktur](abbKennzeichnung.html)
* [Abbildungen im Textbereich](abbTextbereich.html)
* [Verschachtelte Abbildungen](abbVerschachtelt.html)
* [Notenbeispiele](noten.html)


---

## Auflösung von Abkürzungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/abkuerzung.html](https://www.deutschestextarchiv.de/doku/basisformat/abkuerzung.html)

# Auflösung von Abkürzungen

Abkürzungen werden vorlagengetreu übernommen, d.h. sie werden nicht stillschweigend aufgelöst.
Für die Auflösung von Abkürzungen steht das Element `<choice>` mit den
Unterelementen `<abbr>` und `<expan>` zur Verfügung. Dabei
steht in `<abbr>` die Abkürzung, wie sie aus der Vorlage übernommen wurde. In
`<expan>` steht die expandierte Form der Abkürzung.

```
<choice>
  <abbr>[Abkürzung entsprechend der Vorlage]</abbr>
  <expan>[Auflösung/Expansion der Abkürzung]</expan>
</choice>
```

Soll eine Abkürzung nur als solche markiert werden ohne Angabe der zugehörigen Expansion, so
wird das Element `<abbr>` gesetzt. Die Elemente `<choice>`
und `<expan>` entfallen in diesem Fall.

```
<abbr>[Abkürzung entsprechend der Vorlage]</abbr>
```

VORSICHT:

Eine Expansion kann jedoch nie ohne die zugehörige, aus der Vorlage entnommene Abkürzung
stehen (stillschweigende Auflösungen von Abkürzungen sind unzulässig). Das Element
`<expan>` kann somit nie ohne zugehöriges `<choice>` und
`<abbr>` stehen.

Abkürzungen werden generell mit dem im Unicode-Standard dafür vorhandenen Zeichen wiedergegeben.
Findet sich für eine Abkürzung kein Äquivalent im Unicode-Standard, so kann die stellvertretende
Unicode-Entität `&#xFFFC;` (OBJECT REPLACEMENT CHARACTER) gesetzt werden. In diesem Fall sollte
die korrekte Auflösung der betreffenden Abkürzung im Element `<expan>` wiedergegeben
werden.

Zur Kodierung nicht entzifferbarer bzw. nicht interpretierbarer Auflösungen vgl. Kap.
[Schwer bzw. nicht entzifferbare Zeichen und Auslassungen](gapSupplied.html)


---

## Absätze

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/absatz.html](https://www.deutschestextarchiv.de/doku/basisformat/absatz.html)

# Absätze

Die Absatzstruktur wird aus der Vorlage übernommen. Die jeweiligen Absätze werden
mittels `<p>`-Elementen gekennzeichnet.

## Absatz

![](img/XHqxBBsaJ4.png)

```
<p>„Das wird ja ordentlich intereſſant,“ bemerkte Max<lb/>
  Werner und ſtand auf, „da könnte ich am Ende noch hier<lb/>
  für Fenia gegen irgend einen ſibiriſchen Drachen zu Felde<lb/>
  ziehen?“
</p><lb/>
<p>Aber der Onkel teilte die heitere Stimmung nicht;<lb/>
  ſeine Miene blieb ſo feierlich und beſorgt wie zuvor.
</p><lb/>
        
```

*Quelle:
[Andreas-Salome, Lou: Fenitschka. Eine Ausschweifung. Stuttgart, 1898. [Faksimile 48]](http://www.deutschestextarchiv.de/andreas_fenitschka_1898/48)*

Einrückungen der ersten Zeile eines Absatzes bleiben
unberücksichtigt.

Größere Abstände zwischen Absätzen werden nur dann
ausgezeichnet, wenn diesbezüglich innerhalb eines Buches eine
Varianz festzustellen ist. In diesem Fall wird in der betreffenden
Zeile mittels `<space dim="vertical"/>` auf den
signifikanten Abstand hingewiesen (s. auch Kap. [Leerraum](leerraum.html)).

HINWEIS:

***Abweichende Regelung Phase 1:** Einrückungen der ersten Zeile eines Absatzes sowie größere Abstände
zwischen Absätzen bleiben unberücksichtigt.*

## (Sinntragender) Abstand zwischen Absätzen

![](img/dvhEgTfOad.png)

```
<p>[...]<lb/>
  Mu&#x0364;nzpreis, und demnach ein vollkommneres Pfund Ster-<lb/>
  ling hervor gebracht.
</p><lb/>
<p>
  Wo alſo u&#x0364;berhaupt gemu&#x0364;nzt wird, da muß es einen feſten<lb/>
  [...]<lb/>
  und iſt die unumga&#x0364;ngliche Bedingung der Mo&#x0364;glichkeit einer<lb/>
  Mu&#x0364;nze.
</p><lb/>
<space dim="vertical"/>
<p>
  Mu&#x0364;nzen heißt den ſchwankenden Werth der edeln Metalle<lb/>
  befeſtigen; was ko&#x0364;nnte ihn befeſtigen als eine Sache von<lb/>
  [...]
</p>
```

*Quelle:
[Müller,
Adam Heinrich: Versuche einer neuen Theorie des Geldes mit besonderer
Rücksicht auf Großbritannien. Leipzig u. a., 1816. [Faksimile 233]](http://www.deutschestextarchiv.de/mueller_geld_1816/233)*


---

## Formen und Kodierung von Anhängen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/anhAllg.html)

# Formen und Kodierung von Anhängen

Alle Abschnitte des Buches, die auf das Textende
folgen (Anhänge, Register, sonstige Zusätze), werden mit dem
`<back>`-Element umschlossen, das sich im
Anschluss an das `<body>`-Element in
`<text>` befindet. Die Grobstrukturierung
innerhalb des `<back>`-Elements erfolgt mittels
`<div>`-Elementen, deren
`@type`-Attribute die Textbestandteile näher
spezifizieren.

Folgende Werte von `@type` innerhalb des
`<back>`-Bereichs sind möglich:

| `@type`-Wert | Bedeutung |
| --- | --- |
| `postface` | Nachwort, Schlusswort, Epilog |
| `contents` | Inhaltsverzeichnis |
| `imprint` | Angaben zur Druckausgabe |
| `imprimatur` | Druckerlaubnis |
| `index` | Register |
| `corrigenda` | Druckfehlerverzeichnis |
| `appendix` | Anhang (z.B. mit erläuternden Abbildungen oder Tabellen) |
| `bibliography` | Literaturverzeichnis |
| `advertisement` | Anzeige |

Das öffnende `<back>`-Tag folgt direkt auf das schließende
`</body>`-Tag, steht also noch **vor** jedem
neuen Seitenumbruch. Das hintere Vorsatzblatt (Spiegel und fliegendes Blatt)
sowie der hintere Einband sind immer Teil des
`<back>`-Bereichs.

```
<back>
  <div type="corrigenda">
    <head>Verbesserungen:</head>
    <p>Druckfehler ...</p>
  </div>
  <div type="advertisement">
    <head>[Verlagsname]</head>
    <list>
      <item>[Werbestück1]</item>
      <item>[Werbestück2]</item>
    </list>
  </div>
  <div type="imprint">
    <p>[Impressum]</p>
  </div>
</back>
```


---

## Literaturverzeichnis

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhBibliographie.html](https://www.deutschestextarchiv.de/doku/basisformat/anhBibliographie.html)

# Literaturverzeichnis

Das Literaturverzeichnis wird mittels `<div type="bibliography">[...]</div>` umschlossen. Ein möglicher Verzeichnistitel steht zugehörigen im `<head>`-Element. Die einzelnen Literatureinträge werden als Liste (`<list>`) mit unterschiedlichen Listenelementen (`<item>`) umgesetzt.

```
<back>
  <div type="bibliography">
    <head>[Verzeichnistitel]</head>
    <list>
      <item>[bibliographische Angabe 1]</item>
      <item>[bibliographische Angabe 2]</item>
    </list>
  </div>
</back>
```


---

## Mehrere Register am Buchende

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhMehrereReg.html](https://www.deutschestextarchiv.de/doku/basisformat/anhMehrereReg.html)

# Mehrere Register am Buchende

Stehen mehrere Register am Schluss eines Bandes, so wird jedes
Register in einem eigenen Element `<div type="index">` verzeichnet.

```
<back>
  <div n="1" type="index">
    <head>[Titel Register 1]</head>
    <list>
      <item>[Stichwort 1]
        <ref>[Seitenzahl]</ref>
      </item>
    </list>
  </div>
  <div n="1" type="index">
    <head>[Titel Register 2]</head>
    <list>
      <item>[Stichwort 1]
        <ref>[Seitenzahl]</ref>
      </item>
    </list>
  </div>
</back>
```


---

## Einfache Registerform

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhRegEinfach.html](https://www.deutschestextarchiv.de/doku/basisformat/anhRegEinfach.html)

# Einfache Registerform

Register werden mittels `<div>`-Elementen
umschlossen, die das Attribut-Wert-Paar
`@type="index"` erhalten.

Das eigentliche Register wird sodann in Form einer Liste
(`<list>`) strukturiert, wobei jeder
Registereintrag in einem `<item>`-Element
verzeichnet wird.

Die Seitenzahlen im Registereintrag werden innerhalb des
`<item>`-Elements mit einem
`<ref>`-Element umschlossen. Jede Seitenzahl
bekommt ein separates `<ref>`-Element, auch
wenn die Seitenzahlen direkt hintereinander stehen. Eventuelle
Satzzeichen stehen außerhalb der
`<ref>`-Elemente.

Weisen Registereinträge Untereinträge auf, so werden diese als
geschachtelte Listen ausgezeichnet.

```
<back>
  <div type="index">
    <head>[Titel des Registers]</head>
    <list>
      <item>[Stichwort1]
        <ref target="#[Seitenzahl1]">[Seitenzahl1]</ref>
        <ref target="#[Seitenzahl2]">[Seitenzahl2]</ref>
      </item>
      <item>[StichwortX]
        <ref target="#[SeitenzahlX]">[SeitenzahlX]</ref>
      </item>
    </list>
  </div>
</back>
```


---

## Register mit Untertiteln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhRegUntertitel.html](https://www.deutschestextarchiv.de/doku/basisformat/anhRegUntertitel.html)

# Register mit Untertiteln

Ist das Register in verschiedene Unterabschnitte eingeteilt, werden
diese mittels mehreren `<div>`-Elementen
strukturiert.

```
<back>
  <div n="1" type="index">
    <head>[Registertitel]</head>
    <div n="2">
      <head>[Untertitel 1]</head>
      <list>
        <item>[Stichwort]
          <ref>[Seitenzahl]</ref>
        </item>
      </list>
    </div>
    <div n="2">
      <head>[Untertitel 2]</head>
      <list>
        <item>[Stichwort]
          <ref>[Seitenzahl]</ref>
        </item>
      </list>
    </div>
  </div>
</back>
```


---

## Register

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhRegister.html](https://www.deutschestextarchiv.de/doku/basisformat/anhRegister.html)

# Register

## Themen

* [Einfache Registerform](anhRegEinfach.html)
* [Register mit Untertiteln](anhRegUntertitel.html)
* [Mehrere Register](anhMehrereReg.html)


---

## Anhang

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/anhang.html](https://www.deutschestextarchiv.de/doku/basisformat/anhang.html)

# Anhang

## Themen

* [Anhänge Grundstruktur](anhAllg.html)
* [Literaturverzeichnis](anhBibliographie.html)
* [Register](anhRegister.html)


---

## Nutzung des DTA-Basisformat-Schemas

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/benutzungDTABfSchema.html](https://www.deutschestextarchiv.de/doku/basisformat/benutzungDTABfSchema.html)

# Nutzung des DTA-Basisformat-Schemas

## Verfügbarkeit des Schemas

Das **Relax-NG-Schema** des DTA-Basisformats befindet sich unter der Adresse:
<http://www.deutschestextarchiv.de/basisformat.rng>.

Die zugrundeliegende **ODD-Datei** befindet sich unter der Adresse:
<http://www.deutschestextarchiv.de/basisformat.odd>.

Der zugehörige ergänzende **Schematron-Regelsatz** ist zugänglich unter der Adresse:
<http://www.deutschestextarchiv.de/basisformat.sch>.

## Statisches vs. aktuelles Schema

Das DTA-Basisformat ist zwar in seiner Spezifikation weitgehend stabil. Dennoch gibt es immer
wieder Änderungen, die unter Umständen nicht abwärtskompatibel sind, d.h. Dokumente, die
einmal gegen das DTA-Basisformat-Schema unter der Adresse
<http://www.deutschestextarchiv.de/basisformat.rng>
validiert haben, validieren nicht garantiert immer gegen dieses Schema. Deswegen kann es sinnvoll
sein, sich eine lokale Kopie des Schemas zu sichern und diese in den XML-Quellen zu referenzieren.

## Spezifikation des DTABf-Schemas in einer XML-Datei

Eine zum DTA-Basisformat kompatible Datei sollte die Spezifikation des DTABf-Schemas sowie der ergänzenden DTABf-Schematron-Regeln
enthalten. Daraus resultiert die folgende Grundstruktur für DTABf-Dateien:

```
<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="http://www.deutschestextarchiv.de/basisformat.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="http://www.deutschestextarchiv.de/basisformat.sch" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>[Metadaten]</teiHeader>
  <text>[Text]</text>
</TEI>
```

Wenn eine lokale Version des Schemas vorgehalten wird, lautet die Schema-Spezifikation entsprechend:

```
<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="file:/pfad/zur/datei/basisformat.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="file:/pfad/zur/datei/basisformat.sch" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>[Metadaten]</teiHeader>
  <text>[Text]</text>
</TEI>
```

Eine *Vorlagedatei*, die für die Erarbeitung DTA-Basisformat-kompatibler TEI-Dateien zugrunde gelegt werden kann, findet sich unter
<http://www.deutschestextarchiv.de/files/vorlage_basisformat.xml>.

Der kommerzielle XML-Editor **[oXygen](http://www.oxygenxml.com/)** unterstützt die Einbindung eines Schemas in eine XML-Datei mit entsprechenden Oberflächenfunktionen:

![](img/schemaoxygen.png)

Einbinden des DTABf-Schemas in ein XML-Dokument im oXygen-XML-Editor

## Validierung von XML-Dokumenten gegen das DTA-Basisformat

Der [oXygen-XML-Editor](http://www.oxygenxml.com/) validiert die Dokumente direkt während der Bearbeitung gegen das jeweils eingebundene Schema und gibt bei Validierungsproblemen entsprechende Fehlermeldungen aus.

Darüber hinaus existieren diverse Kommandozeilentools, die XML-Dokumente gegen ein Relax-NG-Schema validieren
können. Einige Beispiele dazu:

```
jing http://www.deutschestextarchiv.de/basisformat.rng quelldatei.xml
  
xmlstarlet val -r http://www.deutschestextarchiv.de/basisformat.rng quelldatei.xml
```

Die Validierung gegen das Schematron-Schema kann von der Kommandozeile mit Probatron erfolgen:

```
java -jar probatron.jar quelldatei.xml
```


---

## Besondere Textsorten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/besondereTextsorten.html](https://www.deutschestextarchiv.de/doku/basisformat/besondereTextsorten.html)

# Besondere Textsorten

Auszeichnung spezifischer Textarten und Textsorten (Manuskripte; Zeitungen)

## Themen

* [Auszeichnung von Manuskripten](manuskript.html)
* [Auszeichnung von Zeitungen](zeitung.html)


---

## Bibliographie

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/bibliographie.html](https://www.deutschestextarchiv.de/doku/basisformat/bibliographie.html)

# Bibliographie

Eine Bibliographie innerhalb des Textbereichs (z.B. am
Kapitelbeginn), kann mittels des Elements
`<listBibl>` ausgezeichnet werden. Jede
bibliographische Angabe wird innerhalb von
`<listBibl>` mittels
`<bibl>[...]</bibl>` realisiert. Die
Verwendung des `<listBibl>`-Elements ist
optional.

```
<listBibl>
  <bibl>[bibliographische Angabe 1]</bibl>
  <bibl>[bibliographische Angabe 2]</bibl>
  [...]
  <bibl>[bibliographische Angabe n]</bibl>
</listBibl>
```

## Bibliographie im Textbereich

![](img/A47gRvWiVP.png)

```
<div n="2">
  <head><hi rendition="#b"><hi rendition="#aq">I.</hi> Der Begriff der Volkswirtſchaft.</hi></head><lb/>
  <listBibl>
    <bibl>v. <hi rendition="#g">Hermann</hi>, Staatswirtſchaftliche Unterſuchungen. 1832. 1870. —</bibl>
    <bibl> v. <hi rendition="#g">Mangoldt</hi>, Volks-<lb/>wirtſchaft, in Bluntſchli, St.W. —</bibl>
    <bibl><hi rendition="#g">Knies</hi>, Die politiſche Ökonomie vom Standpunkt der geſchichtlichen<lb/>
      Methode. 1853 u. 1883. —</bibl>
    <bibl><hi rendition="#g">Adolf Wagner</hi>, Grundlegung der allg. oder theor. Volkswirtſchafts-<lb/>
      lehre. 1876. 3. Aufl. 1892—94. —</bibl>
    <bibl><hi rendition="#g">Schäffle</hi>, Das geſellſchaftliche Syſtem der menſchlichen Wirt-<lb/>
      ſchaft. 1873.—</bibl>
    <bibl> v. <hi rendition="#g">Schönberg</hi>, Handbuch der politiſchen Ökonomie. 1882 — 1896 (hauptſächlich die<lb/>
      einleitenden und allgemeinen Abſchnitte von v. Schönberg, v. Scheel und Neumann). —</bibl>
    <bibl><hi rendition="#g">Schmoller</hi>,<lb/>
      Städtiſche, territoriale und ſtaatliche Wirtſchaftspolitik. J. f. G.V. 1884 und Schmoller U. U. —</bibl>
    <bibl><lb/><hi rendition="#g">Bücher</hi>, Entſtehung der Volkswirtſchaft. 1893 u. 1898. —</bibl>
    <bibl> v. <hi rendition="#g">Philippovich</hi>, Grundriß der<lb/>politiſchen Ökonomie. 1893 u. 1898.<lb/>
      <hi rendition="#g">Gerber</hi>, Grundzüge eines Syſtems des deutſchen Staatsrechts. 1865 u. 1869. —</bibl>
    <bibl><hi rendition="#g">van Krieken</hi>,<lb/>Über die ſog. organiſche Staatslehre. 1873. —</bibl>
    <bibl><hi rendition="#g">Gierke</hi>, Die Grundbegriffe des Staatsrechts und die<lb/>
      neueſten Staatsrechtstheorien. Z. f. St.W. 1874.</bibl>
  </listBibl><lb/>
  <p>1. <hi rendition="#g">Vorbemerkung</hi>. Die Volkswirtſchaft, deren allgemeine wiſſenſchaftliche<lb/>[...]</p>
[...]</div>
```

*Quelle: [Schmoller, Gustav: Grundriß der
Allgemeinen Volkswirtschaftslehre. Bd. 1. Leipzig, 1900.
[Faksimile 17]](http://www.deutschestextarchiv.de/schmoller_grundriss01_1900/17)*

## Bibliographische Angaben im Fließtext (Level 3)

Auch im Fließtext kann das Element `<bibl>` verwendet werden, um auf
bibliographische Angaben hinzuweisen. Mithilfe eines darunter geordneten `<ref>`-Elements
kann auf eine externe (ausführlichere) Literaturangabe verwiesen werden. Die Verwendung von `<bibl>` und untergeornetem `<ref>` im Fließtext ist optional (Level 3).

![](img/sandrartBiblRef.jpg)

```
<p>[...] weil man beym Homerus in ſeinen 
  <bibl><ref target="http://ta.sandrart.net/-bibliography-2345">Iliaden</ref></bibl> 
liſet/ daß [...]</p>
```

*Quelle: [Sandrart, Joachim von: L’Academia Todesca. della Architectura, Scultura & Pittura: Oder Teutsche Academie der Edlen Bau- Bild- und Mahlerey-Künste. Bd. 2,3. Nürnberg, 1679.
[Faksimile 7]](http://www.deutschestextarchiv.de/sandrart_academie0203_1679/7)*

Zur Auszeichnung von Literaturverzeichnissen am Buchschluss
(Bibliographie im <back>-Bereich) s. Kap. [Anhang](anhang.html).


---

## Inhaltliche Kodierung des Textkörpers

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/body.html](https://www.deutschestextarchiv.de/doku/basisformat/body.html)

# Inhaltliche Kodierung des Textkörpers

## Themen

* [Textkörper Grundstruktur](bodyAllg.html)
* [Interne Textbezüge](diskontTextpassagen.html)
* [Fußnoten](fussnote.html)
* [Endnoten](endnote.html)
* [Marginalien](marginalie.html)
* [Inhaltszusammenfassung](teaser.html)
* [Bibliographie](bibliographie.html)
* [Nachsatz](nachsatz.html)
* [Zitate und Epigraphe](zitateEpigraphe.html)
* [Gedichte und gebundene Sprache](gedichte.html)
* [Dramen](drama.html)
* [Briefe](brief.html)


---

## Grundstruktur des Textkörpers

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/bodyAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/bodyAllg.html)

# Grundstruktur des Textkörpers

Den eigentlichen Text des Werkes umschließt ein `<body>`-Element.

Das öffnende `<body>`-Tag folgt dabei direkt auf das
schließende `</front>`-Tag, steht also noch
vor jedem neuen Seitenumbruch. Das schließende
`</body>`-Tag steht direkt vor dem öffnenden
`<back>`-Tag, welches wiederum noch vor jedem neuen Seitenumbruch folgt.


---

## Bogensignaturen und Kustoden

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/bogensigKustode.html](https://www.deutschestextarchiv.de/doku/basisformat/bogensigKustode.html)

# Bogensignaturen und Kustoden

Bogensignaturen werden durch den Wert `"sig"` im
`@type`-Attribut des `<fw>`-Elements wiedergegeben. Sie
können zu Beginn oder am Schluss einer Seite stehen.

```
<fw type="sig" place="bottom">[Bogensignatur]</fw>
<fw type="sig" place="top">[Bogensignatur]</fw>
```

Für Kustoden (engl. catch words) steht der Wert `"catch"` im
`@type`-Attribut des `<fw>`-Elements. Kustoden können
sowohl unter dem Textbereich als auch unter dem Fußnotenbereich (als Lesehilfe bei
fortlaufenden Fußnoten) stehen. In beiden Fällen wird die Position mittels des Wertes
`"bottom"` im `@place`-Attribut angegeben:

```
<fw type="catch" place="bottom">[Kustode]</fw>
```

## Bogensignaturen und Kustoden

![](img/Ye95WfO2w9.png)

```
<fw place="bottom" type="sig">
  <hi rendition="#fr">Erſter Theil D</hi>
</fw>
<fw place="bottom" type="catch">
  <hi rendition="#fr">erwecket</hi> 
</fw> <lb/>
```

*Quelle:  [Arndt, Johann: Von wahrem Christenthumb. Bd. 1.
Magdeburg, 1610. [Faksimile 55]](http://www.deutschestextarchiv.de/arndt_christentum01_1610/55)*


---

## Grundstruktur der Kodierung von Briefen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/brAllg.html)

# Grundstruktur der Kodierung von Briefen

Briefe werden mit einem `<div>`-Element umrahmt, welches
zusätzlich zum Attribut `@n` das Attribut-Wert-Paar
`@type="letter"` enthält. Die Auszeichnung von Briefen erfolgt nach
den für unspezifizierte Texte geltenden Regeln. Spezifika der Textsorte Brief
sind der `<opener>` und der `<closer>`.

Der `<opener>` umfasst die für einen Briefbeginn
charakteristischen Angaben von Ort, Datum (`<dateline>`),
Anrede und Empfänger.

Der `<closer>` umfasst die für einen Briefschluss
charakteristischen Angaben von Ort, Datum (`<dateline>`),
Grußformel und Signatur des Absenders.

Die Orts- und Datumsangabe im `<opener>` bzw.
`<closer>` wird mit dem Element
`<dateline>` umschlossen. Die Anrede und die Abschlussformel
werden jeweils mit `<salute>` umschlossen. Die Signatur des
Absenders unter einem Brief steht im `<closer>` im Element
`<signed>`. Die Anordnung der Elemente innerhalb des
`<opener>`- bzw. `<closer>`-Elements ist
variabel und orientiert sich an der Vorlage.

```
<div type="letter">
  <head>[Brieftitel]</head> <!-- sofern vorhanden -->
  <opener><!-- sofern vorhanden -->
    <dateline>[Ort und Datum]</dateline>
    <salute>[Anrede]</salute>
  </opener>
  <p>[Brieftext]</p>
  <p>[Brieftext]</p>
  <closer><!-- sofern vorhanden -->
    <dateline>[Ort und Datum]</dateline>
    <salute>[abschließende Grußformel]</salute>
    <signed>[Unterschrift]</signed>
  </closer>
</div>
```

## Briefkopf

![](img/aLa7uHh7XR.png)

```
<div n="2" type="letter">
  <head>An Karoline von Woltmann, in Prag.</head><lb/>
  <opener>
    <dateline>Karlsruhe, den 7. Januar 1817. Trübes windiges,<lb/>warmes Wetter.</dateline>
  </opener><lb/>
  <p>Alles Gras iſt raus: geſtern ſetzten die Leute ſchon ihre<lb/>
  Ertofflen in die Erde: in Markgraf Ludwigs Garten kommen<lb/>[...]</p>
</div><lb/>
```

*Quelle: [Varnhagen von Ense, Rahel: Rahel.
Ein Buch des Andenkens für ihre Freunde. Bd. 2. Berlin, 1834.
[Faksimile 438]](http://www.deutschestextarchiv.de/varnhagen_rahel02_1834/438)*

## Briefschluss

![](img/ayqhh3uhEx.png)

```
<p>[...] Lebe wohl<lb/>
und laſſe bald wieder von Dir hören.</p><lb/>
<closer>
  <dateline>Weimar, den 5. Februar 1810.</dateline><lb/>
  <salute>Goethe.</salute>
</closer><lb/>
```

*Quelle: [Arnim, Bettina von: Goethe's
Briefwechsel mit einem Kinde. Bd. 2. Berlin, 1835. [Faksimile
166]](http://www.deutschestextarchiv.de/arnimb_goethe02_1835/166)*


---

## Briefähnliche Berichte

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brBericht.html](https://www.deutschestextarchiv.de/doku/basisformat/brBericht.html)

# Briefähnliche Berichte

Grußformeln, Datums- und Ortsangaben in briefähnlichen Textpassagen
(z.B. in Vorreden an den Leser, Vorworten, Einleitungen) werden wie
in Briefen behandelt.

## Datumsangaben in briefähnlichen Berichten

![](img/xZkvMl_Ycr.png)

```
<div n="1">
  <head>V.</head><lb/>
  <opener>
    <dateline>
          Auf dem Berge <placeName>Hissarlik</placeName>, 24. November 1871.
        </dateline>
  </opener><lb/>
  <p>Seit meinem Bericht vom 18. und 21. d. M. habe ich,<lb/>
trotz des fortwährenden Regenwetters, noch drei Tage<lb/>
gearbeitet; leider aber sehe ich mich jetzt gezwungen,<lb/>[...]
</p>
</div><lb/>
```

*Quelle: [Schliemann, Heinrich: Trojanische
Alterthümer. Bericht über die Ausgrabungen in Troja. Leipzig,
1874. [Faksimile 103]](http://www.deutschestextarchiv.de/schliemann_trojanische_1874/103)*


---

## Briefe als Einschübe im Prosatext

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brEinschub.html](https://www.deutschestextarchiv.de/doku/basisformat/brEinschub.html)

# Briefe als Einschübe im Prosatext

Briefe und briefähnliche Passagen können in Prosawerken in den
Fließtext eingeschoben erscheinen. In diesen Fällen muss das Element
`<floatingText>` verwendet werden, das wiederum
ein Unterelement `<body>` enthält, innerhalb
dessen die Briefauszeichnung erfolgt. Dem
`<div>`-Element wird **keine**
`@n`-Ebene zugeordnet.

```

  <floatingText>
  <body>
  <div type="letter"></div>
  </body>
  </floatingText>

```

## Brief als Einschub

![](img/aFjBgPCjJu.png)

```
<p>[...] Chlorkalkes zu erfahren. Hierauf verpflichtete mich Liebig<lb/>
mit folgender Antwort:</p><lb/>
<floatingText>
  <body>
    <div type="letter">
      <opener>
        <dateline>München, 21. März 1859.</dateline><lb/>
        <salute>Euer Wohlgeboren!</salute>
      </opener><lb/>
      <p>Beehre ich mich auf Ihr Schreiben zu erwiedern, dass<lb/>
die Hinweglassung Ihrer Beobachtung über das Kindbett-<lb/>
fieber aus der neuen Auflage meiner chemischen Briefe nicht<lb/>
den Grund hat, dass ich die Wichtigkeit Ihrer Erfahrung<lb/>
nicht wie früher anerkenne, sondern weil sie jetzt so be-<lb/>
kannt und verbreitet ist, dass ihre Beibehaltung in meinem<lb/>
Buche zwecklos erscheint, in einem eigentlichen Zusammen-<lb/>
hange damit steht sie nicht. Es ist dies mit anderen Nachträ-<lb/>
gen ebenfalls geschehen.</p><lb/>
      <p>Der Chlorkalk besitzt unzweifelhaft eine desinficirende<lb/>
Eigenschaft.</p>
      <closer>
        <salute>Ergebenst hochachtungsvoll der Ihrige</salute><lb/>
        <signed>Gustav Liebig.</signed>
      </closer>
    </div><lb/>
  </body>
</floatingText>
<p><hi rendition="#c">Bernard Seyfert</hi><lb/>
hat ergänzende Bemerkungen zu dem früher beurtheilten Auf-<lb/>
satze Scanzoni’s geliefert.</p><lb/>
```

*Quelle: [Semmelweis, Ignaz Philipp: Die
Ätiologie, der Begriff und die Prophylaxe des Kindbettfiebers.
Pest u. a., 1861. [Faksimile 435]](http://www.deutschestextarchiv.de/semmelweis_kindbettfieber_1861/435)*


---

## Mehrtägige Briefe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brMehrereTage.html](https://www.deutschestextarchiv.de/doku/basisformat/brMehrereTage.html)

# Mehrtägige Briefe

Einen Spezialfall bilden Briefe, die über mehrere Tage verfasst
wurden, somit mehrere Daten auch innerhalb des Brieftextes
beinhalten. In diesem Fall kann das Element
`<dateline>` außerhalb von
`<opener>` oder `<closer>`
gesetzt und auch innerhalb des Brieftextes verwendet werden:

```
<div n="[Ebene]">
  <head>[Brieftitel]</head><!-- sofern vorhanden -->
  <opener>
    <salute>[Anrede]</salute>
  </opener>
  <dateline>[Datum]</dateline>
  <p>[Brieftext]</p>
  <dateline>[Datum]</dateline>
  <p>[Brieftext]</p>
  <closer>
    <salute>[abschließende Grußformel]</salute>
  </closer>
</div>
```


---

## Postskriptum

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brPostscriptum.html](https://www.deutschestextarchiv.de/doku/basisformat/brPostscriptum.html)

# Postskriptum

Den Angaben des `<closer>`-Elements kann in
Briefen ein Postscriptum folgen, das mittels eines
`<postscript>`-Elements ausgezeichnet wird.
Enthält ein Brief mehrere Postscripta, so kann das
`<postscript>`-Element mehrfach in Folge
verwendet werden. Der Text des Postscriptums wird in
`<p>`-Elementen wiedergegeben. Die mögliche
Kennzeichnung des Postscriptums im Text z.B. durch die Abkürzung
'PS' wird nicht gesondert ausgezeichnet:

```
<postscript>
  <p>[Text des Postscriptums]</p>
  <p>[ggf. weiterer Text des Postscriptums]</p>
</postscript>
<postscript> <!-- ggf. weiteres Postscriptum -->  
  <p>[Text des Postscriptums]</p>
  <p>[ggf. weiterer Text des Postscriptums]</p>
</postscript>
```

## Postskriptum

![](img/x_ionEd6bu.png)

```
<p>[...]<lb/>
  bald durch ihr Spiel darthun. Ich grüße herzlich Woltmann!<lb/>
  Varnhagen Sie beide! Ihre alte wie Sie mich kennen
</p><lb/>
<closer>
  <salute>Rahel.</salute>
</closer><lb/>
<postscript>
  <p>Bald kommt Frühling und Veilchen! Ich pflücke Ih-<lb/>nen eins!</p>
</postscript><lb/>
<postscript>
  <p>Mein Prager Bruder Ludwig iſt geſtern nach Stuttgart<lb/>
  gereiſt, kommt in einem Monat wieder zu mir. Ich habe<lb/>
  <hi rendition="#g">viele</hi> Leute kennen lernen. Wangenheim, Rückert. Franzo-<lb/>
  ſen. Alles!</p>
</postscript><lb/>
```

*Quelle: [Varnhagen von Ense, Rahel: Rahel.
Ein Buch des Andenkens für ihre Freunde. Bd. 2. Berlin, 1834.
[Faksimile 442]](http://www.deutschestextarchiv.de/varnhagen_rahel02_1834/442)*


---

## Unterbrechungen im Briefschluss

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brUnterbrCloser.html](https://www.deutschestextarchiv.de/doku/basisformat/brUnterbrCloser.html)

# Unterbrechungen im Briefschluss

Innerhalb des `<closer>`-Elements sind mehrere
gleichartige Unterelemente möglich, die ggf. mit den Attributen
`@xml:id`, `@next` und
`@prev` verknüpft werden müssen.

## Unterbrechung bei `//signed`

![](img/KWh8cE69eP.png)

```
<closer>
  <salute xml:id="a01" next="a02">
    Mit innigſter Verehrung mich unter-<lb/>zeichnend<lb/>
    <hi rendition="#b">Ew. Durchlaucht</hi>
  </salute><lb/>
  <dateline>Weimar<lb/>den 30. Januar 1808.</dateline><lb/>
  <salute xml:id="a02" prev="a01">untertha&#x0364;nigſter</salute><lb/>
  <signed>
    <hi rendition="#b">J. W. v. <hi rendition="#g">Goethe</hi>.</hi>
  </signed>
</closer><lb/>
```

*Quelle: [Goethe, Johann Wolfgang von: Zur
Farbenlehre. Bd. 1. Tübingen, 1810. [Faksimile
14]](http://www.deutschestextarchiv.de/goethe_farbenlehre01_1810/14)*

Ferner können miteinander korrespondierende
`<salute>`- und
`<signed>`-Elemente voneinander getrennt
stehen. In diesem Fall wird die Verbindung mittels der Attribute
`@xml:id` und `@corresp`
hergestellt.

## Unterbrechung von `//salute` und `//signed` im Briefschluss

![](img/q3xQw3Lved.png)

```
<p>Ich habe nichts dagegen einzuwenden, wenn Sie von den<lb/>
vorstehenden Mittheilungen jeglichen Gebrauch machen.</p><lb/>
<closer>
  <salute xml:id="a01" next="a02">Mit vorzüglicher Hochachtung<lb/>Ihr ergebenster</salute><lb/>
  <dateline>Paderborn den 17./2. 1858.</dateline><lb/>
  <signed xml:id="a02" prev="a01">
    D. <hi rendition="#g">Everken</hi>,<lb/>Director des königl. Hebammeninstitutes.
  </signed>
</closer><lb/>
```

*Quelle: [Semmelweis, Ignaz Philipp: Die
Ätiologie, der Begriff und die Prophylaxe des Kindbettfiebers.
Pest u. a., 1861. [Faksimile 480]](http://www.deutschestextarchiv.de/semmelweis_kindbettfieber_1861/480)*

Zum Umgang mit unterbrochenen Textpassagen vgl. Kap. [Unterbrechungen zusammenhängender Textbestandteile](diskontTextpassagen.html).


---

## Briefe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/brief.html](https://www.deutschestextarchiv.de/doku/basisformat/brief.html)

# Briefe

## Themen

* [Briefe Grundstruktur](brAllg.html)
* [Mehrtägige Briefe](brMehrereTage.html)
* [Postskriptum](brPostscriptum.html)
* [Unterbrechungen im Briefschluss](brUnterbrCloser.html)
* [Briefähnliche Berichte](brBericht.html)
* [Briefe als Einschübe im Prosatext](brEinschub.html)


---

## Hinweise zum Datenschutz

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/datenschutz](https://www.deutschestextarchiv.de/doku/basisformat/datenschutz)

# Hinweise zum Datenschutz

## Allgemeine Hinweise der BBAW

Es gelten die Datenschutzbestimmungen der Berlin-Brandenburgischen Akademie der Wissenschaften (BBAW), die im folgenden aufgeführt sind:

## Nutzung von Matomo (vormals Piwik)

Diese Website benutzt Matomo (vormals Piwik), eine Open-Source-Software zur statistischen Auswertung der Besucherzugriffe. Matomo verwendet sog. “Cookies”, Textdateien, die auf Ihrem Computer gespeichert werden und die eine Analyse der Benutzung der Website durch Sie ermöglichen. Die durch den Cookie erzeugten Informationen über Ihre Benutzung dieses Internetangebotes werden auf einem Server der Berlin-Brandenburgischen Akademie der Wissenschaften in Deutschland gespeichert. Die IP-Adresse wird sofort nach der Verarbeitung und vor deren Speicherung anonymisiert.


---

## Hinweise zum Datenschutz

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/datenschutz.html](https://www.deutschestextarchiv.de/doku/basisformat/datenschutz.html)

# Hinweise zum Datenschutz

## Allgemeine Hinweise der BBAW

Es gelten die Datenschutzbestimmungen der Berlin-Brandenburgischen Akademie der Wissenschaften (BBAW), die im folgenden aufgeführt sind:

## Nutzung von Matomo (vormals Piwik)

Diese Website benutzt Matomo (vormals Piwik), eine Open-Source-Software zur statistischen Auswertung der Besucherzugriffe. Matomo verwendet sog. “Cookies”, Textdateien, die auf Ihrem Computer gespeichert werden und die eine Analyse der Benutzung der Website durch Sie ermöglichen. Die durch den Cookie erzeugten Informationen über Ihre Benutzung dieses Internetangebotes werden auf einem Server der Berlin-Brandenburgischen Akademie der Wissenschaften in Deutschland gespeichert. Die IP-Adresse wird sofort nach der Verarbeitung und vor deren Speicherung anonymisiert.


---

## Datumsangaben

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/datum.html](https://www.deutschestextarchiv.de/doku/basisformat/datum.html)

# Datumsangaben

Datumsangaben des Textes können mit den Elementen
`<date>` und `<dateline>`
ausgezeichnet werden (Level 3).

Dabei repräsentiert `<date>` ein Datum. Mit `<dateline>` kann
eine Datumszeile ausgezeichnet werden, die z.B. auch eine Ortsangabe enthalten kann.

## `<date>`

![](img/roseggerDate.png)

```
<div>[...]
  <p>
    <date> <hi rendition="#et">Am Jakobitag 1817.</hi> </date>
  </p><lb/>
  <p>Heute bin ich wieder im Hinterwinkel, im<lb/>
    Hauſe des Mathes geweſen. [...]
  </p><lb/>
[...]</div>
```

*Quelle: [Rosegger, Peter: Die Schriften des Waldschulmeisters. Pest, 1875. [Faksimile 212]](http://www.deutschestextarchiv.de/rosegger_waldschulmeister_1875/212)*

## `<dateline> (1)`

![](img/386597dateline.png)

```
<div>[...]
  <p>Es werden alſo hierdurch [...]</p><lb/>
  <dateline><hi rendition="#c">Dreßden den 20. April 1740.</hi></dateline>
</div>
```

*Quelle: [Schöttgen, Christian: Lebens-Beschreibung Herrn Wolffgang Eulenbecks. Dresden, 1740. [Faksimile 12]](http://www.deutschestextarchiv.de/386597/12)*

## `<dateline> (2)`

![](img/arnimbDate.png)

```
<milestone rendition="#hr" unit="section"/>
<div n="2">
  <dateline>
    <hi rendition="#et">Am frühſten Morgen auf dem Johannisberg.</hi>
  </dateline><lb/>
  <p>Das Sonnenlicht ſtiehlt ſich durch dieſe Büſche in<lb/>
  [...]</p><lb/>
[...]</div>
```

*Quelle: [[Arnim, Bettina von]: Tagebuch. Berlin, 1835. [Faksimile 21]](http://www.deutschestextarchiv.de/arnimb_goethe03_1835/21)*

Achtung:

Die Elemente `<date>` und `<dateline>`
sind teilweise in unterschiedlichen Elementkontexten erlaubt, d.h. `<date>` ist
nicht notwendigerweise überall dort valide, wo auch `<dateline>` valide ist. Zu den
Elementkontexten, in welchen diese Elemente jeweils benutzt werden können s. die TEI-Dokumentation zu
`<dateline>` und `<date>`.

Das Element `<date>` kann auch innerhalb von
`<dateline>` stehen, um das eigentliche Datum in der
Datumszeile separat auszuzeichnen.

## `<date>` in `<dateline>` (1)

![](img/wissmannDate.png)

```
<div>[...]
  <p>Die beiden Schlusskapitel [...]</p><lb/>
  <closer>
    <cb type="start"/>
    <dateline>
      <placeName>Gut Weissenbach<lb/>
      bei Liezen in Steiermark.</placeName><lb/>
      <date>Herbst 1900.</date>
    </dateline>
    <cb/>
    <signed>Dr. v. Wissmann.</signed><lb/>
    <cb type="end"/>
  </closer>
</div>
```

*Quelle: <http://www.deutschestextarchiv.de/wissmann_afrika_1901/6>*

## `<date>` in `<dateline>` (2)

![](img/siemensDateDateline.png)

```
<div>[...]<p>Der Verfasser hat seine Zustimmung und seine Mithülfe nicht<lb/>
versagt.</p><lb/>
  <closer>
    <dateline><placeName>Berlin</placeName>,  
      <date>im August 1881</date>.
    </dateline><lb/> 
    <hi rendition="#b #right">Die Verlagshandlung.</hi> 
  </closer>
</div>
```

*Quelle: [Siemens, Werner von: Gesammelte Abhandlungen und Vorträge. Berlin, 1881. [Faksimile 15].](http://www.deutschestextarchiv.de/siemens_abhandlungen_1881/15)*

Tipp:

Für weitere Verwendungsbeispiele s. auch die Dokumentationen zu
[Briefen](brAllg.html).


---

## Bezüge zwischen Textbestandteilen eines Dokuments

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/diskontTextpassagen.html](https://www.deutschestextarchiv.de/doku/basisformat/diskontTextpassagen.html)

# Bezüge zwischen Textbestandteilen eines Dokuments

Aufeinander Bezug nehmende Textteile, die durch Elementgrenzen voneinander getrennt sind,
werden miteinander verknüpft. Dabei sind zweierlei Bezüge möglich:

## Title

* [Einschub](einschub.html)
* [Korrespondierende Textpassagen](parallelePassagen.html)


---

## Texteinteilung auf Kapitelebene

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/div.html](https://www.deutschestextarchiv.de/doku/basisformat/div.html)

# Texteinteilung auf Kapitelebene

Die Texteinteilung (z.B. Kapitel, Abschnitte, Teile ...) eines Buches
wird mittels verschachtelter `<div>`-Elemente
dargestellt. Diese enthalten in der Regel ein Attribut
`@n`, welches die Strukturebene angibt.

```
<div n="1">
<head>[Titel Kapitel 1]</head><!-- sofern vorhanden -->
<div n="2">
<head>[Titel Unterkapitel 1.1]</head><!-- sofern vorhanden -->
<p>[Text]</p>
<p>[Text]</p>
    ...
</div>
</div>
```

Darüber hinaus kann für Textabschnitte mit besonderer Struktur das
Attribut `@type` eingesetzt werden, welches diese näher
spezifiziert.

Folgende Werte kann das `@type`-Attribut dabei
annehmen:

|  |  |
| --- | --- |
| `abbreviations` | Abkürzungsverzeichnis |
| `act` | Akt im Drama |
| `advertisement` | Anzeige |
| `appendix` | Anhang |
| `bibliography` | Bibliographie |
| `chapter` | Kapitel (Level 3) |
| `contents` | Inhaltsverzeichnis |
| `copyright` | Hinweise zum Copyright |
| `corrigenda` | Druckfehlerverzeichnis |
| `dedication` | Widmung |
| `diaryEntry` | Tagebucheintrag (Level 3) |
| `edition` | Abdruck einer externen Textquelle (Level 3) |
| `figures` | Verzeichnis der Abbildungen |
| `frontispiece` | Frontispiz |
| `imprint` | Impressum |
| `imprimatur` | Druckerlaubnis |
| `index` | Register |
| `letter` | Brief (Level 3) |
| `poem` | Gedicht |
| `postface` | Schlusswort, Nachwort, Epilog (Level 3) |
| `preface` | Geleitwort, Vorwort, Einleitung (Level 3) |
| `recipe` | Rezept (Level 3) |
| `scene` | Szene im Drama |

In der Regel sind Dokumente durch `<div>`-Elemente strukturiert. Ausnahmen sind
jedoch möglich. Zum Beispiel können Gedichtbände gänzlich mit `<lg>`s strukturiert
werden (s. Kapitel [Gedichte](gedichte.html)).

Die Titel der (Unter-)Kapitel werden mit dem `<head>`-Element umschlossen.
Dabei ist es unerheblich, ob der jeweilige Titel als Überschrift auf einer eigenen Zeile steht,
oder am Beginn der ersten Kapitelzeile erscheint. Die Abstände zwischen Überschriften verschiedener
Ebenen, die Ausrichtung der Überschriften (z.B. zentriert) sowie eventueller Frakturwechsel
werden nicht gesondert ausgezeichnet. Hingegen werden Zeilenumbrüche, alle typographischen
Besonderheiten (fett, kursiv, gesperrt etc.) sowie ein Wechsel zur Antiqua-Schrift ausgezeichnet.

## Kapitelstrukturierung

![](img/FTcrVmt7dM.png)

```
<div n="1">
   <head>IV.<lb/>Die Brauchbarkeit der Durchschnittszahlen.</head><lb/>
   <milestone rendition="#hr" unit="section"/><lb/>
   <div n="2">
      <head>§ 17.<lb/><hi rendition="#b">Gruppierung der Versuchsresultate.</hi></head><lb/>
      <p>Die erste Frage, welche aus den in der beschriebenen<lb/>
      Weise angestellten Untersuchungen eine Antwort erwartet,<lb/>
      ist nach den Erörterungen von §§ 7 und 8 die nach der<lb/>
      Natur der gewonnenen Durchschnittszahlen. Sind die immer-<lb/>
      hin schwankenden Zeiten, welche erforderlich waren, um<lb/>
      Reihen von bestimmter Länge <hi rendition="#g">unter möglichst gleichen<lb/>
      Umständen</hi> gerade auswendig zu lernen, so gruppiert, daſs<lb/>
      man ihre Mittelwerte mit Wahrscheinlichkeit als Maſszahlen<lb/>
      im physikalischen Sinne ansehen darf oder nicht?</p>
   </div>
</div><lb/>
```

*Quelle: [Ebbinghaus, Hermann: Über das Gedächtnis. Leipzig, 1885. [Faksimile 63]](http://www.deutschestextarchiv.de/ebbinghaus_gedaechtnis_1885/63)*

Grundsätzlich erfolgt die `<div>`-Strukturierung
als Kapiteleinteilung. Werden in der Vorlage zusätzlich weitere
Strukturierungsansätze verfolgt, so werden diese der Kapiteleinteilung
untergeordnet, jedoch nach Möglichkeit mit abgebildet.

## Verschiedene Strukturierungsansätze auf Kapitelebene

![](img/YE7waC5HwX.png)

```
<div n="2">
   <head>
      <hi rendition="#b"><hi rendition="#aq">IV.</hi> Milch- und Waſſerſuppen.</hi>
   </head><lb/>
   <div n="3">
      <head>45. Milchſuppe.</head><lb/>
      <p>Ein Maß Milch, einen Eßlöffel voll Stärke oder Kartoffel-<lb/>
      mehl, Zitronenſchale oder auch ein Paar friſche Pfirſichblätter,<lb/>[...]</p>
   </div>
</div><lb/>
```

*Quelle: [Davidis, Henriette:
Praktisches Kochbuch für die gewöhnliche und feinere Küche.
4. Aufl. Bielefeld, 1849. [Faksimile 82]](http://www.deutschestextarchiv.de/davidis_kochbuch_1849/82)*

Untergeordnete `<div>`-Container enden entweder
mit dem Beginn einer neuen *division* gleicher Ebene
oder mit dem Ende der übergeordneten *division*.
Eingeschobene `<div>`-Container, nach deren
Abschluss die übergeordnete *division* weitergeführt
wird, sind nicht möglich. Es gibt jedoch Fälle, in welchen die
Möglichkeit, den Textfluss durch eine *division* zu
unterbrechen und am Schluss der eingeschobenen
*division* wieder aufzunehmen, notwendig ist. In
diesen Fällen wird das Element `<floatingText>`
eingesetzt, innerhalb dessen die eingeschobende
*division* realisiert wird.

## Einschub

![](img/9i_izyOAE4.png)

```
<div n="1">
   <p>[...]<pb facs="#f0173" n="163"/>
   ebenfalls in das Dintenfaß zu ſchauen, um den Grund<lb/>
   der Zögerung zu erfahren. Endlich aber iſt Eliſe mit<lb/>
   ihren Vorbereitungen fertig und ſchreibt:</p><lb/>
   <floatingText>
      <body>
         <div type="letter">
            <opener>
               <salute><hi rendition="#et">Lieber Guſtav!</hi></salute>
            </opener><lb/>
            <p>„Dein Brief iſt glücklich angekommen. Flämm-<lb/>
            „chen hat ihn gebracht. Die alte Martha hat einen<lb/>
            „naſſen Waſchlappen im Fenſter liegen; ſie will Dich<lb/>
            „tüchtig waſchen, wenn Du kommſt. Den Onkel<lb/>
            „kann ich nicht feſtbinden, er rennt heute immer in<lb/>
            „der Stube auf und ab und ſitzt keinen Augenblick<lb/>
            „ſtill. Du ſollſt erſt Dein Exercitium fertig machen<lb/>
            „und es mit bringen, eher ſoll ich nicht kommen!<lb/>
            „Mach’ ſchnell!!! Meine Taſche bringe ich mit!“ —</p><lb/>
            <closer>
               <salute><hi rendition="#et">Eliſe.</hi></salute>
            </closer>
         </div>
      </body>
   </floatingText><lb/>
   <p>Auch dieſe Botſchaft wird dem Flämmchen umge-<lb/>
   hängt — die Praxis hat es gelehrig gemacht; zwitſchernd<lb/>
   ſchüttelt es das Köpfchen, als wolle es ſagen, nuniſt’s<lb/>[...]</p>
</div>
```

*Quelle: [Raabe, Wilhelm: Die Chronik
der Sperlingsgasse. Berlin, 1857. [Faksimile
173]](http://www.deutschestextarchiv.de/raabe_sperlingsgasse_1857/173)*


---

## Die Strukturierung in Akte/Aufzüge und Szenen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drAktSzene.html](https://www.deutschestextarchiv.de/doku/basisformat/drAktSzene.html)

# Die Strukturierung in Akte/Aufzüge und Szenen

Akte/Aufzüge werden in `<div>`-Elemente eingefasst, die ein Attribut `@type` mit dem Wert `"act"` enthalten. Die einzelnen
Szenen/Auftritte stehen in einem untergeordneten `<div>`-Element, welches das Attribut-Wert-Paar `@type="scene"` enthält.

```
<div n="[Ebene]" type="act">
  <head>[Titel Aufzug]</head>
  <div n="[untergeordnete Ebene]" type="scene">
    <head>[Titel Auftritt 1]</head>
    <!-- sämtliche Elemente und Textbestandteile des 1. Auftritts -->
  </div>
  <div n="[untergeordnete Ebene]" type="scene">
    <head>[Titel Auftritt 2]</head>
    <!-- sämtliche Elemente und Textbestandteile des 2. Auftritts -->
  </div>
</div>
```


---

## Bühnenanweisungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drBuehnenanweisung.html](https://www.deutschestextarchiv.de/doku/basisformat/drBuehnenanweisung.html)

# Bühnenanweisungen

Bühnenanweisungen werden mit einem
`<stage>`-Element umschlossen:

```
<stage>[Bühnenanweisung]</stage>
```

Verschiedene Arten von Bühnenanweisungen sind möglich und werden
verschiedenartig behandelt:

**1. Bühnenanweisungen am Beginn eines Aufzugs oder Auftritts:**
Diese Bühnenanweisungen treffen Festlegungen für den folgenden
Abschnitt. Sie stehen in der Regel im Anschluss an die jeweilige
Abschnittsüberschrift.

```
<div type="[z.B. scene]">
  <head>[Titel des Auftritts]</head>
  <stage>[Bühnenanweisung]</stage>
  <sp>[Sprechakt]</sp>
  <sp>[weiterer Sprechakt]</sp>
</div>
```

## Bühnenanweisung I

![](img/GQfzrOTco5.png)

```
<div n="2">
  <head><hi rendition="#g">Erſter Akt</hi>.</head><lb/>
  <stage><hi rendition="#g">Der königliche Garten in Aranjuez</hi>.</stage><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <div n="3">
    <head><hi rendition="#g">Erſter Auftritt</hi>.</head><lb/>
    <stage><hi rendition="#g">Dom Karlos. Domingo</hi>.</stage><lb/>
    <sp who="#DOMI">
      <speaker><hi rendition="#g">Domingo</hi>.</speaker><lb/>
      <p><hi rendition="#in">D</hi>ie ſchönen Tage in Aranjuez<lb/>
      ſind nun zu Ende. Eure königliche Hoheit<lb/>[...]</p>
    </sp>
  [...]</div>
</div>
```

*Quelle: [Schiller, Friedrich: Dom Karlos,
Infant von Spanien. Leipzig, 1787. [Faksimile 13]](http://www.deutschestextarchiv.de/schiller_domkarlos_1787/13)*

**2. Bühnenanweisungen vor dem Beginn oder nach dem Schluss eines
Sprechakts:** Bühnenanweisungen innerhalb eines Aufzugs, die
keinem Sprechakt zugeordnet sind, sondern sich auf die Szene im
Allgemeinen beziehen, werden außerhalb der angrenzenden
`<sp>`-Elemente in einem
`<stage>`-Element wiedergegeben.

```
<div type="[z.B. scene]">
  <head>[Titel des Auftritts]</head>
  <sp>[Sprechakt]</sp>
  <stage>[Bühnenanweiung]</stage>
  <sp>[weiterer Sprechakt]</sp>
</div>
```

## Bühnenanweisung II

![](img/gLovGqjkrN.png)

```
<sp who="#JHERR">
  <speaker>
    <hi rendition="#b">Der junge Herr.</hi>
  </speaker><lb/>
  <p>Ah ja, Marie, ah ja, ich hab’ geläutet, ja …<lb/>
    was hab’ ich nur … ja richtig, die Rouletten<lb/>
    lassen S’ herunter, Marie … Es ist kühler,<lb/>
    wenn die Rouletten unten sind .... ja ....</p>
</sp><lb/>
<stage>(Das Stubenmädchen geht zum Fenster und läßt die<lb/>
Rouletten herunter.)</stage><lb/>
<sp who="#JHERR">
  <speaker>
    <hi rendition="#b">Der junge Herr</hi>
  </speaker>
  <stage>(liest weiter.)<lb/></stage>
  <p>
    Was machen S’ denn, Marie? Ah ja. Jetzt<lb/>
    sieht man aber gar nichts zum Lesen.
  </p>
</sp><lb/>
```

*Quelle: [Schnitzler, Arthur: Reigen. Wien,
1903. [Faksimile 41]](http://www.deutschestextarchiv.de/schnitzler_reigen_1903/41)*

**3. Bühnenanweisungen innerhalb eines Sprechakts:**
Bühnenanweisungen, die einem Sprechakt zugeordnet sind, werden
innerhalb des `<sp>`-Elements wiedergegeben.
Steht die Bühnenanweisung **vor bzw. hinter der wörtlichen Rede**
des Sprechers, wird sie außerhalb von `<p>`
wiedergegeben. Steht sie **innerhalb der wörtlichen Rede**, so
wird das `<p>`-Element **nicht**
unterbrochen. Statt dessen wird das
`<stage>`-Element in das
`<p>`-Element integriert.

```
<div type="[z.B. scene]">
  <head>[Titel des Auftritts]</head>
  <sp>
    <speaker>[Sprecher]</speaker>
    <stage>[Bühnenanweiung vor der Rede]</stage>
    <p>[Rede] 
      <stage>[Bühnenanweiung innerhalb der Rede]</stage> 
    [Rede]</p>
    <stage>[Bühnenanweiung nach der Rede]</stage>
  </sp>
  <sp>[weiterer Sprechakt]</sp>
</div>
```

## Bühnenanweisung III

![](img/bjk8xsoRgn.png)

```
<sp who="#ANA">
  <speaker>
    <hi rendition="#b">Anatol.</hi>
  </speaker>
  <p>
    Ruhig <stage>(zu Cora)</stage> … Schlafen … feſt, tief ſchlafen.<lb/>
    <stage>(Er ſteht eine Weile vor Cora, die ruhig athmet und ſchläft).</stage> 
    So … nun<lb/>kannſt Du fragen.
  </p>
</sp><lb/>
```

*Quelle: [Schnitzler, Arthur: Anatol.
Berlin, 1893. [Faksimile 27]](http://www.deutschestextarchiv.de/schnitzler_anatol_1893/27)*


---

## Figurenaufstellung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drFiguren.html](https://www.deutschestextarchiv.de/doku/basisformat/drFiguren.html)

# Figurenaufstellung

Die dem Drama vorangestellte Auflistung der mitwirkenden Figuren wird
mittels `<div n="[Ebene]">` ausgezeichnet. Ist
die Auflistung der Figuren mit einem entsprechenden Titel versehen,
so wird dieser innerhalb des `<div>`-Elements
in einem `<head>`-Element wiedergegeben. Die
eigentliche Liste der Figuren wird mittels eines
`<castList>`-Elements ausgezeichnet. Jede
gelistete Figur wird innerhalb der `<castList>`
mit einem `<castItem>`-Element umschlossen.

```
<div n="[Ebene]">
  <head>[Titel der Figurenaufstellung]</head><!-- falls vorhanden -->
  <castList>
    <castItem>[Figur 1]</castItem>
    <castItem>[Figur 2]</castItem>
  </castList>
</div>
```

Der Name der jeweiligen Figur steht in einem
`<role>`-Element, welches dem
`<castItem>`-Element untergeordnet ist. Ein
Attribut `@xml:id` innerhalb des
`<role>`-Elements weist der Figur eine
eindeutige Identifikation zu. Eine der Figur ggf. zugeordnete
Funktion wird innerhalb von `<castItem>` in
einem `<roleDesc>`-Element wiedergegeben.

```

  <castItem>
    <role xml:id="[ID]">[Name der Figur]</role>
    <roleDesc>[Funktion]</roleDesc><!-- falls vorhanden -->
  </castItem>

```

Gruppen von Figuren, denen in der Vorlage gemeinsam eine Funktion
zugeordnet wird (in der Regel graphisch durch Klammerung
dargestellt), werden innerhalb der `<castList>`
mit einem `<castGroup>`-Element umschlossen.
Die den Figuren einer Gruppe gemeinsame Funktion wird innerhalb der
`<castGroup>` in einem
`<roleDesc>`-Element realisiert. Jede Figur
wird mit einem `<castItem>`-Element
umschlossen, welches die oben beschriebenen Funktionen aufweist.

```
<castGroup>
  <roleDesc>[Funktion]</roleDesc>
  <castItem><role xml:id="[ID]">[Figur 1]</role></castItem>
  <castItem><role xml:id="[ID]">[Figur 2]</role></castItem>
</castGroup>
```

## Figurenaufstellung I

![](img/j_i8JBjJxE.png)

```
<castList>
  <head>
    <hi rendition="#c"><hi rendition="#g">Perſonen</hi>.</hi>
  </head><lb/>
  <castItem>
    <role xml:id="JUP"><hi rendition="#g">Jupiter</hi>,</role>
    <roleDesc>in der Geſtalt des Amphitryon.</roleDesc>
  </castItem><lb/>
  <castItem>
    <role xml:id="MER"><hi rendition="#g">Merkur</hi>,</role>
    <roleDesc>in der Geſtalt des Soſias.</roleDesc>
  </castItem><lb/>
  <castItem>
    <role xml:id="AMP"><hi rendition="#g">Amphitryon</hi>,</role>
    <roleDesc>Feldherr der Thebaner.</roleDesc>
  </castItem><lb/>
  <castItem>
    <role xml:id="SOS"><hi rendition="#g">Soſias</hi>,</role>
    <roleDesc>ſein Diener.</roleDesc>
  </castItem>
</castList><lb/>
```

*Quelle: [Kleist, Heinrich von: Amphitryon.
Dresden, 1807. [Faksimile 17]](http://www.deutschestextarchiv.de/kleist_amphytrion_1807/17)*

Um Klammerungen innerhalb von `<castGroup>`
anzuzeigen, wird das `@rendition`-Attribut verwendet,
welches die Werte `#rightBraced`,
`#leftBraced`, `#bottomBraced`,
`#topBraced"` erhalten kann (vgl. Kap. [Klammerungen](klammerung.html)).

## Klammerung in Figurenaufstellungen

![](img/4le9MRBrlh.png)

```
<castList>
  <castItem>
    <role xml:id="ATT"><hi rendition="#g">Attus Tullus</hi>, Oberfeldherr.</role>
  </castItem><lb/>
  <castGroup rendition="#rightBraced">
    <castItem>
      <role xml:id="LUC">
        <hi rendition="#g">Lucumo</hi>
      </role>
    </castItem><lb/>
    <castItem>
      <role xml:id="VOLT">
        <hi rendition="#g">Volturio</hi>
      </role>
    </castItem><lb/>
    <castItem>
      <role xml:id="ARU">
        <hi rendition="#g">Aruntius</hi>
      </role>
    </castItem><lb/>
    <castItem>
      <role xml:id="POR">
        <hi rendition="#g">Porus</hi>
      </role>
    </castItem>
    <roleDesc>Feldherren.</roleDesc>
  </castGroup>
</castList><lb/>
```

*Quelle: [Collin, Heinrich Joseph von:
Coriolan. Berlin, 1804. [Faksimile 11]](http://www.deutschestextarchiv.de/collin_coriolan_1804/11)*

Einen Spezialfall stellen Nennungen von Schauspielern dar, die in
einer Aufführung des Dramas eingesetzt wurden. Diese Schauspieler
werden mit dem `<actor>`-Element ausgezeichnet:

```
<castItem>
  <role xml:id="[ID]">[Figur]</role>
  <roleDesc>[Funktion]</roleDesc><!-- falls vorhanden -->
  <actor>[Schauspieler]</actor>
</castItem>
```

## Figurenaufstellung mit Nennung des Schauspielers/der Schauspielerin

![](img/HiXXMapbCd.png)

```
<castList>
  <head>
    <hi rendition="#c">Perſonen.</hi>
  </head><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <p>
    <hi rendition="#c">Beſetzung im k. k. priv. Theater an der Wien.</hi>
  </p><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <castItem>
    <role xml:id="GRI">
      <hi rendition="#b">Grillhofer,</hi>
    </role>
    <roleDesc>ein reicher Bauer.</roleDesc>
    <space dim="horizontal"/>
    <actor>
      <hi rendition="#et">Herr Martinelli.</hi>
    </actor>
  </castItem><lb/>
  <castItem>
    <role xml:id="DUS">
      <hi rendition="#b">Duſterer,</hi>
    </role>
    <roleDesc>ſein Schwager.</roleDesc>
    <space dim="horizontal"/>
    <actor>
      <hi rendition="#et">〃 Frieſe.</hi>
    </actor>
  </castItem>
</castList><lb/>
```

*Quelle: [Anzengruber, Ludwig: Der
G'wissenswurm. Wien, 1874. [Faksimile 11]](http://www.deutschestextarchiv.de/anzengruber_gwissenswurm_1874/11)*


---

## Sprechakte

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drSprechakt.html](https://www.deutschestextarchiv.de/doku/basisformat/drSprechakt.html)

# Sprechakte

## Themen

* [Sprechakt und Rede](drSprechaktRede.html)
* [Verse im Drama](drVers.html)
* [Synchrone Sprechakte](drSprechaktSynchron.html)
* [Gemeinsame Sprechakte](drSprechaktGem.html)
* [Gruppen von Sprechakten](drSprechaktGruppe.html)


---

## Gemeinsame Sprechakte

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktGem.html](https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktGem.html)

# Gemeinsame Sprechakte

Kommen unterschiedliche Sprecher im Drama gleichzeitig zu Wort, wobei der Wortlaut
ihrer Reden unterschiedlich ist, so werden diese "gemeinsamen Sprechakte"
mittels `<spGrp>` umschlossen.

Oft weist auf die Gleichzeitigkeit eine Klammerung zwischen den betreffenden
Sprechakten hin, die entsprechend mittels des Attribut-Wert-Paares
`@rendition="#leftBraced | #rightBraced"` im `<spGrp>`-Element
kodiert wird.

## Kodierung gemeinsamer Sprechakte mit Klammerung

![](img/robertKlammerung.png)

```
<spGrp rendition="#leftBraced">
  <sp who="#ZOB">
    <speaker>Zobea und die Weiber.</speaker><lb/>
    <p>Weh 
      <list rendition="#leftBraced #rightBraced">
        <item>mein</item><lb/>
        <item>ihr</item>
      </list>
      Vater 
      <list rendition="#rightBraced #leftBraced">
        <item>meine</item><lb/>
        <item>ihre</item>
      </list>
      Brüder!<lb/>
      Wildes Feuer, Ströme Blut!
    </p><lb/>
  </sp>
  <sp who="#SIN">
    <speaker>Sinabal.</speaker><lb/>
    <p>Senget, brennet alles nieder,<lb/>
      Mordet der Verräther Brut!
    </p>
  </sp>
</spGrp><lb/>
```

*Quelle: [Robert, Ludwig: Die Sylphen. Berlin, 1806.
[Faksimile 103]](http://www.deutschestextarchiv.de/dtaq/book/view/25229?p=103)*

Tipp:

Zur Kodierung von Klammerungen vgl. Kap.
[Klammerungen](klammerung.html).


---

## Gruppen von Sprechakten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktGruppe.html](https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktGruppe.html)

# Gruppen von Sprechakten

Werden im Drama mehrere Sprechakte gruppiert (z.B. durch
Klammerungen), um ihnen dieselbe Bühnenanweisung zuzuordnen, so
werden die Sprechakte im Element `<spGrp>`
(speech group) zusammengefasst.

Dabei steht innerhalb von `<spGrp>` jeder
Sprechakt in einem separaten `<sp>`-Element.
Die übergeordnete Bühnenanweisung steht direkt in einem
`<stage>`-Element in
`<spGrp>`. Eine eventuelle Klammerung wird in
diesem `<stage>`-Element durch das
Attribut-Wert-Paar `@rendition="#leftBraced"` bzw.
`@rendition="#rightBraced"` wiedergegeben.

```
<spGrp>
    <stage rendition="#rightBraced">[Bühnenanweisung mit Klammerung um die gruppierten Sprechakte]</stage>
    <sp>[Sprechakt 1]</sp>
    <sp>[Sprechakt 2]</sp>
    <sp>[Sprechakt n]</sp>
  </spGrp>
```

## Gruppen von Sprechakten

![](img/WOFMgEWnPE.png)

```
<spGrp>
  <stage rendition="#rightBraced #v">(Sehr raſch).</stage>
  <sp who="#WEI">
    <speaker><hi rendition="#g">Weiring</hi>.</speaker><lb/>
    <p>Was willſt Du denn? —</p>
  </sp><lb/>
  <sp who="#CHR">
    <speaker><hi rendition="#g">Chriſtine</hi>.</speaker><lb/>
    <p>Laß mich, ich will fort</p>
  </sp><lb/>
  <sp who="#WEI">
    <speaker><hi rendition="#g">Weiring</hi>.</speaker><lb/>
    <p>Wohin willſt Du?</p>
  </sp><lb/>
  <sp who="#CHR">
    <speaker><hi rendition="#g">Chriſtine</hi>.</speaker><lb/>
    <p>Zu ihm … zu ihm …</p>
  </sp><lb/>
  <sp who="#WEI">
    <speaker><hi rendition="#g">Weiring</hi>.</speaker><lb/>
    <p>Aber was fällt Dir denn ein</p>
  </sp><lb/>
  <sp who="#CHR">
    <speaker><hi rendition="#g">Chriſtine</hi>.</speaker><lb/>
    <p>Du verſchweigſt mir irgend was — laß<lb/>mich hin —</p>
  </sp>
</spGrp><lb/>
```

*Quelle: [Schnitzler, Arthur: Liebelei.
Berlin, 1896. [Faksimile 136]](http://www.deutschestextarchiv.de/schnitzler_liebelei_1896/136)*

Tipp:

Zur Kodierung von Klammerungen vgl. Kap.
[Klammerungen](klammerung.html).


---

## Sprechakt und Rede

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktRede.html](https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktRede.html)

# Sprechakt und Rede

Sprechakte werden in ein `<sp>`-Element eingebettet. In einem
`@who`-Attribut wird die ID des jeweiligen Sprechers verzeichnet (zur
Sprecher-ID s. [oben](drFiguren.html)). Der im Text genannte Sprechername
steht innerhalb von `<sp>` im Element `<speaker>`.

Die eigentliche Rede wird in `<p>`-Elementen
wiedergegeben.

```
<sp who="#[Sprecher-ID]">
  <speaker>[Sprecher]</speaker>
  <p>[Text]</p>
</sp>
```

## Sprechakt und Rede

![](img/9Sqye98fs2.png)

```
<sp who="#DAN">
  <speaker>
    <hi rendition="#g">Danton</hi>
  </speaker>
  <stage>(zu Camille.)</stage><lb/>
  <p>Ruhig, mein Junge, du haſt dich heiſer geſchrien.</p>
</sp><lb/>
```

*Quelle: [Büchner, Georg: Danton's Tod.
Frankfurt (Main), 1835. [Faksimile 152]](http://www.deutschestextarchiv.de/buechner_danton_1835/152)*


---

## Synchrone Sprechakte

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktSynchron.html](https://www.deutschestextarchiv.de/doku/basisformat/drSprechaktSynchron.html)

# Synchrone Sprechakte

Text, der durch mehrere Sprecher gleichzeitig wiedergegeben wird
(synchroner Sprechakt) wird in nur einem
`<sp>`-Element wiedergegeben. Die verschiedenen
Sprecher stehen gemeinsam in einem
`<speaker>`-Element. Wird die gemeinsame Rede
durch eine Klammerung verdeutlicht, so erhält je nach Ort der
Klammerung das betreffende Element ein Attribut-Wert-Paar
`@rendition="#rightBraced"` bzw.
`@rendition="#leftBraced"` (zur Kodierung von
Klammerungen vgl. Kap. [Klammerungen](klammerung.html).

```
<sp who="#[Sprecher-ID 1] #[Sprecher-ID n]">
  <speaker>[Sprecher 1, Sprecher n]</speaker>
  <stage>[Bühnenanweisung]</stage>
  <p>[Text]</p>
</sp>
```

## Synchrone Sprechakte

![](img/BtFj0SpBKU.png)

```
<sp who="#WUNGE #WEIN">
  <speaker>
    <hi rendition="#fr">W. Ungew.<lb/>Weinhold.</hi>
  </speaker>
  <stage rendition="#leftBraced">(verwundert.)</stage>
  <p>Abrechnung?</p>
</sp><lb/>
```

*Quelle: [Gotter, Friedrich Wilhelm: Die
Erbschleicher. Leipzig, 1789. [Faksimile 170]](http://www.deutschestextarchiv.de/gotter_erbschleicher_1789/170)*

Tipp:

Zur Kodierung von Klammerungen vgl. Kap.
[Klammerungen](klammerung.html).


---

## Verse im Drama

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drVers.html](https://www.deutschestextarchiv.de/doku/basisformat/drVers.html)

# Verse im Drama

Auch bei in Versform geschriebenen Dramen wird die Rede in
`<p>`-Elementen wiedergegeben.

## Verse im Drama

![](img/JtghjG0qAj.png)

```
<sp who="#FAU">
  <speaker><hi rendition="#g">Fauſt</hi>.</speaker><lb/>
  <p>Es klopft? Herein! Wer will mich wieder plagen?</p> 
</sp><lb/> 
<sp who="#MEP"> 
  <speaker><hi rendition="#g">Mephiſtopheles</hi>.</speaker><lb/> 
  <p>Ich bin's.</p> 
</sp><lb/> 
<sp who="#FAU"> 
  <speaker><hi rendition="#g">Fauſt</hi>.</speaker><lb/> 
  <p><hi rendition="#et">Herein!</hi></p>
</sp><lb/> 
<sp who="#MEP"> 
  <speaker><hi rendition="#g">Mephiſtopheles</hi>.</speaker><lb/> 
  <p><hi rendition="#et">Du mußt es dreymal ſagen,</hi></p>
</sp><lb/>
```

*Quelle: [Goethe, Johann Wolfgang von:
Faust. Eine Tragödie. Tübingen, 1808. [Faksimile
103]](http://www.deutschestextarchiv.de/goethe_faust01_1808/103)*

Durch Sprecherwechsel bedingte Unterbrechungen von Versen können
durch Verknüpfung der umschließenden
`<p>`-Elemente mittels der Attribute
`@xml:id`, `@prev` und
`@next` wiedergegeben werden (s. Kap.: [Unterbrechungen zusammenhängender Textbestandteile](diskontTextpassagen.html)).

Achtung:

Diese Form der tieferen Texterschließung wurde
für die Werke des DTA-Korpus nicht angewandt.

Gereimte Passagen oder Gesänge innerhalb eines in Prosaform
verfassten Dramas werden hingegen als Versgruppen
(`<lg>`) gekennzeichnet.


---

## Dramen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/drama.html](https://www.deutschestextarchiv.de/doku/basisformat/drama.html)

# Dramen

## Themen

* [Figurenaufstellung](drFiguren.html)
* [Akte und Szenen](drAktSzene.html)
* [Bühnenanweisungen](drBuehnenanweisung.html)
* [Sprechakte](drSprechakt.html)


---

## Editorische Eingriffe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/editorEingriff.html](https://www.deutschestextarchiv.de/doku/basisformat/editorEingriff.html)

# Editorische Eingriffe

## Themen

* [Editorische Eingriffe Grundstruktur](eeAllg.html)
* [Druckfehler](eeDruckfehler.html)
* [Abkürzungen](abkuerzung.html)
* [Normalisierungen](normalisierung.html)
* [Sachkommentar](sachkommentar.html)


---

## Grundstruktur der Kodierung editorischer Eingriffe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/eeAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/eeAllg.html)

# Grundstruktur der Kodierung editorischer Eingriffe

Editorische Eingriffe, im Zuge derer Textvarianten zu
spezifischen Schreibungen der Vorlage angegeben werden, werden im Element
`<choice>` verzeichnet. Das Element
`<choice>` kann dabei verschiedene Unterelemente
enthalten, welche die Art des Eingriffs spezifizieren. Diese werden in den
folgenden Kapiteln erläutert.

Das Element `<choice>` steht grundsätzlich für die Annotation von Schreibungen
der Vorlage und zugehörigen, durch den Editor gegebenen alternativen Schreibungen
zur Verfügung. Daraus ergibt sich, dass `<choice>` immer mindestens zwei
Unterelemente enthalten muss.

## Spannweite des `<choice>`-Elements

Grundsätzlich werden editorische Eingriffe auf Wortebene
vorgenommen, d.h. die Annotation mithilfe des
`<choice>`-Elements bezieht sich jeweils auf ein
vollständiges Wort. Dabei kann sich das
`<choice>`-Element auch über den Zeilenrand
erstrecken.

Außer dem `<lb>`-Element steht jedoch
kein zusätzliches Material im `<choice>`-Element,
d.h. es erstreckt sich z.B. **nicht** über den Seitenrand, über
Anmerkungen, Abbildungen etc.

Bezieht sich eine Korrektur auf Wörter, die
durch "unbeteiligtes" Material auf der Seite unterbrochen werden, so wird
lediglich der von dem editorischen Eingriff betroffene Wortteil in
`<choice>` behandelt.

Andersherum kann das
`<choice>`-Element mehrere Wörter zugleich
umschließen, wenn der editorische Eingriff sich auf die Getrennt- bzw.
Zusammenschreibung bezieht. In diesem Fall werden alle beteiligten Wörter
in das `<choice>`-Element aufgenommen.


---

## Druckfehler

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/eeDruckfehler.html](https://www.deutschestextarchiv.de/doku/basisformat/eeDruckfehler.html)

# Druckfehler

Die Texte werden vorlagengetreu abgeschrieben. Sofern jedoch im
Erschließungsprozess Druckfehler zuverlässig erkannt werden, können
diese verbessert werden. Hierfür wird das
`<choice>`-Element verwendet. Es enthält ein
Element `<sic>`, das die fehlerhafte Form
dokumentiert und ein Element `<corr>`,
innerhalb dessen die Berichtigung erfolgt.

```
<choice>
  <sic>[fehlerhafte Form]</sic>
  <corr>[verbesserte Form]</corr>
</choice>
```

Einer als fehlerhaft markierten Form muss immer eine Korrektur
beigegeben werden, d.h. das Element `<sic>`
kann nie ohne zugehöriges `<choice>` und
`<corr>` stehen.

## Korrektur von Druckfehlern I

![](img/J7kQzhfMI3.png)

```
Er fuhr <choice><sic>unn</sic><corr>nun</corr></choice> fort:
```

*Quelle: [Kerner, Justinus: Geschichten
Besessener neuerer Zeit. Karlsruhe, 1834. [Faksimile
106]](http://www.deutschestextarchiv.de/kerner_besessene_1834/106)*

## Korrektur von Druckfehlern II

![](img/ofEixtGxVX.png)

```
<choice>
  <sic>mittlerr</sic>
  <corr>mittlern</corr>
</choice>
```

*Quelle: [Rössig, Carl Gottlob: Versuch
einer pragmatischen Geschichte der Ökonomie- Polizey- und
Cameralwissenschaften. Deutschland. Bd. 1. Leipzig, 1781.
[Faksimile 30]](http://www.deutschestextarchiv.de/roessig_oekonomie01_1781/30)*

Um zu beschreiben, auf welche Quelle die Klassifizierung einer
Schreibung als Druckfehler zurückgeht, kann dem Element
`<corr>` ein Attribut `@type`
beigegeben werden, welches die folgenden Werte annehmen kann:

|  |  |
| --- | --- |
| `"addenda"` | in den Addenda des betreffenden Werkes verzeichnete Fehlstelle |
| `"corrigenda"` | im Verzeichnis der Corrigenda des betreffenden Werkes vermerkter Druckfehler |
| `"editorial"` | durch den Bearbeiter/Editor ermittelter Druckfehler |

Diese Angabe, um welche Art der Korrektur es sich handelt, ist
fakultativ (Level 3).

Infolge von Druckfehlern können neue Zeichen entstehen, die keine
Entsprechung im zugehörigen Alphabet haben (z.B. umgedrehtes "e").
Diese Zeichen werden, auch wenn ein entsprechendes oder ähnliches
Zeichen im Unicode-Zeichensatz vorhanden ist, nicht wiedergegeben.
Statt dessen steht die Unicode-Entität U+FFFC (*placeholder in
text for an otherwise unspecified object*). Auf diese Weise wird
das Vorhandensein des Druckfehlers dokumentiert, wobei dieser jedoch
nicht mit ggf. abweichender Semantik (z.B. e-Schwa für umgedrehtes
e) reproduziert wird.

## Korrektur von Druckfehlern III

![](img/knR6AisjCf.png)

```
Glauben zu <choice><sic>find&#xfffc;n</sic><corr>finden</corr></choice>, wenn
```

*Quelle: [Forster, Georg: Johann Reinhold Forster's [...] Reise um die Welt. Bd. 1. Berlin, 1778. [Faksimile 464]](http://www.deutschestextarchiv.de/forster_reise01_1778/464)*


---

## Eigennamen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/eigenname.html](https://www.deutschestextarchiv.de/doku/basisformat/eigenname.html)

# Eigennamen

Die Auszeichnung von Eigennamen (Level 3) erfolgt in auf die Semantik
der jeweiligen Eigennamen spezifizierten Elementen:

* `<persName>`: Personenname
* `<orgName>`: Name einer Organisation
* `<placeName>`: Ortsname
* `<name type="artificialWork">`: Benennung
  eines Kunstwerks oder Gebäudes

Dabei wird das Element `<persName>` nicht weiter
unterstrukturiert (d.h. es erfolgt beispielsweise keine weitere
Unterscheidung zwischen Vorname und Familienname einer Person).
Namenszusätze, die **nicht** in der Quelle stehen, werden in der
Transkription **nicht** wiedergegeben.

Alle genannten Eigennamen-Elemente können ein Attribut
`@ref` enthalten. Dieses erhält als Wert eine
eindeutige URI, welche auf eine externe Ressource verweist, die den
betreffenden Eigennamen näher spezifiziert (z.B. Verweise auf die
Gemeinsame Normdatei GND, den Getty-Thesaurus oder eine eigens
zusammengestellte Eigennamen-Datenbank).

## Eigennamen I

![](img/Q7aiY3wZJJ.png)

```
<persName ref="http://d-nb.info/gnd/118710788">Papst Innocenz X.</persName>
```

*Quelle: [[Berg, Albert]: Die preussische
Expedition nach Ost-Asien. Bd. 3. Berlin, 1873. [Faksimile
35]](http://www.deutschestextarchiv.de/berg_ostasien03_1873/35)*

## Eigennamen II

![](img/hUh2gsmazm.png)

```
<persName ref="http://isni-url.oclc.nl/isni/0000000081390848">Lindesay Brine</persName> und <persName ref="http://isni-url.oclc.nl/isni/0000000083618666">Andrew Wilson</persName>.
```

*Quelle: [[Berg, Albert]: Die preussische
Expedition nach Ost-Asien. Bd. 3. Berlin, 1873. [Faksimile
15]](http://www.deutschestextarchiv.de/berg_ostasien03_1873/15)*

**Trunkierte Eigennamen** (z.B. Nord- und Ostsee) werden als
solche markiert, indem ein Attribut-Wert-Paar
`@full="abb"` (für "Abkürzung") in das jeweils
umschließende Eigennamen-Element aufgenommen wird.

```
<placeName full="abb">Nord-</placeName> und <placeName>Ostsee</placeName>
```

Auf die vollständige Form des durch Trunkierung abgekürzten
Eigennamens zeigt der Verweis auf eine externe Ressource im
`@ref`-Attribut (s. oben). Der vervollständigte
Eigenname kann daneben auch im Text mithilfe des
`<choice>`-Elements mit den Unterelementen
`<orig>` und `<reg>`
wiedergegeben werden.

```
<placeName full="abb">
  <choice>
    <orig>Nord-</orig>
    <reg>Nordsee</reg>
  </choice>
</placeName>
und <placeName>Ostsee</placeName>

```

Zur Verwendung von `<choice>` s. auch Kap. [Editorische Eingriffe](editorEingriff.html)


---

## Einfärbungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/einfaerbung.html](https://www.deutschestextarchiv.de/doku/basisformat/einfaerbung.html)

# Einfärbungen

## Einfärbungen

![](img/JQw2LBhAI6.png)

```
<l><hi rendition="#in #red">I</hi>ch schrieb es auf: 
   nicht länger sei verhehlt</l><lb/>
<l><hi rendition="#blue">W</hi>as als gedanken ich nicht mehr verbanne</l><lb/>
```

*Quelle: [George, Stefan: Das Jahr der Seele. Berlin,
1897. [Faksimile 15]](http://www.deutschestextarchiv.de/george_seele_1897/15)*


---

## Einführung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/einfuehrung.html](https://www.deutschestextarchiv.de/doku/basisformat/einfuehrung.html)

# Einführung

Zielsetzung des DTA-Basisformats, zugehörige Publikationen, Nutzung und erste Schritte

Auf den folgenden Seiten wird das TEI/XML-Basisformat des DTA (DTABf) bereitgestellt, welches die
Grundlage für die Annotation sämtlicher Volltexte des DTA-Korpus bildet.
Es soll im Rahmen der DTA-Richtlinien, die daneben auch die allgemeinen
[Leitlinien des DTA](http://www.deutschestextarchiv.de/doku/leitlinien) sowie die
[Transkriptionsrichtlinien](http://www.deutschestextarchiv.de/doku/richtlinien) beinhalten,
eine möglichst umfassende Textaufbereitung erlauben und dabei gleichzeitig Variationsspielräume bei der Annotation
so einschränken, dass die Kohärenz der DTA-Texte untereinander gewährleistet wird.

Das DTA-Basisformat folgt den P5-Richtlinien der [Text Encoding Initiative](http://www.tei-c.org/)
(TEI), welche für die Annotation historischer gedruckter Werke in einem Korpus spezifiziert, dabei aber nicht erweitert werden.


---

## Eingerückter Text

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/einrueckung.html](https://www.deutschestextarchiv.de/doku/basisformat/einrueckung.html)

# Eingerückter Text

Eingerückter Text wird ebenfalls mit dem
`@rendition`-Attribut gekennzeichnet, welches in das
`<hi>`-Element oder ein Blockelement der DTA-Elementauswahl
eingebettet ist. Die Position des Textes wird als Wert des
`@rendition`-Attributs übermittelt:

| Attribut-Wert-Paar | Bedeutung |
| --- | --- |
| `rendition="#et"` | eingerückter Text |
| `rendition="#c"` | zentriert |
| `rendition="#right"` | rechtsbündig |

HINWEIS:

***Abweichende Regelung Phase 1:** Eingerückter Text wird mit dem `<hi>`-Element
ausgezeichnet. Die Position des Textes wird im
`@rendition`-Attribut in Form eines der oben genannten Werte übermittelt.*

Einrückungen und Zentrierungen in Überschriften, Listen und Tabellen werden im DTA-Korpus
in der Regel nicht gesondert ausgezeichnet. Eine Ausnahme bilden die mittels OCR erfassten
Texte.

Achtung:

Im nachfolgenden Beispiel finden sich neben eingerücktem Text verschiedene weitere Formatierungen
(i.e. gesperrt, fett, rechtsbündig).

## Einrückung

![](img/LsJVxtnwNz.png)

```
<p>
   <hi rendition="#et"><hi rendition="#g">Heidelberg,</hi> den 15. Juli 1892.</hi>
</p><lb/>
<p>
   <hi rendition="#right #b">E. Kraepelin.</hi>
</p><lb/>
```

*Quelle: [Kraepelin, Emil: Ueber die Beeinflussung
einfacher psychischer Vorgänge durch einige Arzneimittel. Jena, 1892.
[Faksimile 14]](http://www.deutschestextarchiv.de/kraepelin_arzneimittel_1892/14)*


---

## Einschübe und diskontinuierliche Textpassagen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/einschub.html](https://www.deutschestextarchiv.de/doku/basisformat/einschub.html)

# Einschübe und diskontinuierliche Textpassagen

Die Verknüpfung der separierten Textbestandteile
erfolgt durch die Attribute
`@prev` und
`@next` unter
Zuhilfenahme von
`@xml:id`'s.

Wird die Textpassage mehrfach unterbrochen, so werden
jeweils die aufeinanderfolgenden Teile
miteinander verknüpft, wobei der erste Teil
der Kette kein `@prev` und
der letzte Teil kein `@next`
enthält.

Beispiel: Paralleldruck zweier Texte auf den einander
gegenüberliegenden Buchseiten

```
<div xml:id="[ID text1_teil1]" next="#[ID text1_teil2]">...</div>
<pb/>
<div xml:id="[ID text2_teil1]" next="#[ID text2_teil2]">...</div>
<pb/>
<div xml:id="[ID text1_teil2]" prev="#[ID text1_teil1]">...</div>
<pb/>
<div xml:id="[ID text2_teil2]" prev="#[ID text2_teil1]">...</div>
```

Achtung:

Zu den Konventionen für die `@xml:id`-Werte beachten
Sie bitte die [XML-Richtlinie des W3C](http://www.w3.org/TR/REC-xml/#id).

## Nebeneinander geordnete selbständige Texte

![](img/WV66RAboye.png)
![](img/rRcqzO3Trc.png)

```
<row>
  <cell xml:id="text1_teil1" next="#text1_teil2">
    Die Martingale um die Kummete der<lb/>
  </cell>
  <cell xml:id="text2_teil1" next="#text2_teil2">
    Die Martingale um die Kummete der<lb/>
  </cell>
</row>
<pb n="61" facs="#f0075"/>
<fw type="header" place="top">Vierspännige Luxus-Equipagen.</fw><lb/>
<row>
  <cell xml:id="text1_teil2" prev="#text1_teil1">
    Hinterpferde herum und nicht nur durch die<lb/>
    Kummetschliessergelenke durchgezogen.<lb/>
  </cell>
  <cell xml:id="text2_teil2" prev="#text2_teil1">
    Hinterpferde herum und nicht nur durch die<lb/>
    Kummetschliessergelenke durchgezogen-<lb/>
  </cell>
</row>
```

*Quelle: [Wrangel, Carl Gustav: Das Luxus-Fuhrwerk. Stuttgart, 1898. [Faksimile 74/75]](http://www.deutschestextarchiv.de/wrangel_luxusfuhrwerk_1898/75)*

Tipp:

Typische Beispiele für diskontinuierliche Textpassagen sind etwa
[Fortlaufende Fußnoten](fnFortlaufend.html),
[Endnoten](endnote.html),
[Diskontinuierliche Vers-Teile in Gedichten](geDiskontVerse.html).

HINWEIS:

***Abweichende Regelung Phase 1:** Fortlaufende Fußnoten sowie
Endnoten stellen einen Spezialfall für die
Unterbrechnung zusammengehöriger
Textpassagen dar, der mittels des
`<seg>`-Elements
behandelt wird (s. dazu Kap. [Fortlaufende Fußnoten](fnFortlaufend.html) und [Endnoten](endnote.html)).*


---

## Wiedergabe der Endnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/enKodierung.html](https://www.deutschestextarchiv.de/doku/basisformat/enKodierung.html)

# Wiedergabe der Endnoten

Die Endnotentexte werden jeweils an der Stelle wiedergegeben, an der
sie tatsächlich stehen. Sie werden mit dem
`<note>`-Element ausgezeichnet, das die
Attribute `@place` (Wert: `end`) und
`@n` (Wert: die Endnotenreferenz im Text) sowie eine
`@xml:id` und einen Verweis auf das zugehörige
Endnotenzeichen mittels `@prev` enthält:

```
<note place="end" n="[Endnotenreferenz]" xml:id="[ID 02]" prev="#[ID 01]">[Endnotentext]</note>
```

Formatierungen, Spalten- und Zeilenumbrüche im Endnotentext werden
wie im Haupttext gehandhabt.

Enthält eine Endnote wiederum eine Fußnote, so wird diese gemäß den
Richtlinien für Fußnoten ausgezeichnet.

## Endnotenreferenz im Text

![](img/buZKg5fBGd.png)

```
<note place="end" n="78)" xml:id="a02" prev="#a01">
  Vergl. Autenrieth über das Gift der Fische, Tübingen 1833, wo die früheren<lb/>
  Nachrichten zusammengestellt und beurtheilt sind.
</note><lb/>
```

*Quelle: [Martens, Eduard von: Die preussische Expedition nach Ost-Asien. Nach amtlichen Quellen.
Zoologischer Teil. Erster Band. Berlin, 1876. [Faksimile 377]](http://www.deutschestextarchiv.de/berg_ostasienzoologie01_1876/377)*

HINWEIS:

***Abweichende Regelung Phase 1:** Die
Endnotentexte werden jeweils an der Stelle wiedergegeben, an der sie
tatsächlich stehen. Sie werden mit dem
`<note>`-Element ausgezeichnet, das die
Attribute `@place` (Wert: `end`) und
`@n` (Wert: die Endnotenreferenz im Text)
enthält:*

```
<note place="end" n="[Endnotenreferenz]">[Endnotentext]</note>
```


---

## Verweise auf Endnoten im Text

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/enVerweis.html](https://www.deutschestextarchiv.de/doku/basisformat/enVerweis.html)

# Verweise auf Endnoten im Text

Der Verweis auf eine Endnote im Text wird mit
dem `<note>`-Element ausgezeichnet, das eine
`@xml:id` und einen Verweis auf das zugehörige
Endnotenzeichen mittels `@next` enthält:

```
<note place="end" n="[Endnotenreferenz]" xml:id="[ID 01]" next="#[ID 02]"/>
```

Das referenzierende Zeichen wird textgetreu
wiedergegeben; besondere Formatierungen des Endnotenzeichens
(Hoch-/Tiefstellung, gesperrter Druck …) bleiben dabei
unberücksichtigt.

## Wiedergabe der Endnotenreferenz im Text

![](img/UwY7n5VZAN.png)

```
<p>[...] wegen gewarnt; wir gebrauchten die Vorsicht, die rauhe Haut zu<lb/>
  entfernen, assen aber das weisse Fleisch 
  ohne allen Nachtheil.<note place="end" n="78)" xml:id="a01" next="#a02"/>
</p><lb/>
```

*Quelle: [Martens, Eduard von: Die
preussische Expedition nach Ost-Asien. Nach amtlichen Quellen.
Zoologischer Teil. Erster Band. Berlin, 1876. [Faksimile
342]](http://www.deutschestextarchiv.de/berg_ostasienzoologie01_1876/342)*

HINWEIS:

***Abweichende Regelung Phase 1:** Der Verweis auf eine
Endnote im Text wird nicht gesondert als solcher ausgezeichnet.
Typographische Besonderheiten des Endnotenzeichens werden jedoch wie
gewohnt berücksichtigt.*


---

## Endnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/endnote.html](https://www.deutschestextarchiv.de/doku/basisformat/endnote.html)

# Endnoten

## Themen

* [Verweise auf Endnoten im Text](enVerweis.html)
* [Wiedergabe der Endnoten](enKodierung.html)


---

## Epigraphe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/epigraph.html](https://www.deutschestextarchiv.de/doku/basisformat/epigraph.html)

# Epigraphe

Epigraphe können auf der Titelseite oder am Beginn eines Kapitels oder Abschnitts stehen.
Zur Kodierung s. [Zitate und Epigraphe](zitateEpigraphe.html).


---

## Epigraphe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/epigraphe.html](https://www.deutschestextarchiv.de/doku/basisformat/epigraphe.html)

# Epigraphe

## Allgemeines

Epigraphe, d.h. Sinnsprüche am Beginn eines Buches, Kapitels oder
Abschnittes, werden mit dem Element
`<epigraph>` ausgezeichnet. Der eigentliche
Epigraphtext wird, wenn es sich um Prosatext handelt, in Paragraphen
(`<p>`) wiedergegeben. Handelt es sich um ein
Epigraph in Versform, so wird es durch das
`<lg>`-Element umrahmt (s. Kap. [Zitate/Epigraphe als Versgruppen](zeVers.html)).

## Epigraph, das kein Zitat darstellt:

```
<epigraph>
  <p>[Epigraphtext]</p>
</epigraph>
```

## Epigraphe, die keine Zitate sind

![](img/rdDfXDNxcs.png)

```

<epigraph>
  <p>Audiatur et altera pars.</p>
</epigraph>
```

*Quelle: [Curtius, Georg: Zur Kritik der
neuesten Sprachforschung. Leipzig, 1885. [Faksimile
98]](http://www.deutschestextarchiv.de/curtius_sprachforschung_1885/98)*

## Zitat als Epigraph ohne Nennung des Urhebers:

```
<epigraph>
  <quote>[Zitattext]</quote>
</epigraph>
```

## Zitat als Epigraph ohne Nennung des Urhebers

![](img/uKIglJOHU5.png)

```
<epigraph>
  <quote>„De subjecto vetustissimo<lb/>
  novissimam promovemus scientiam.“</quote>
</epigraph><lb/>
```

*Quelle: [Ebbinghaus, Hermann: Über das
Gedächtnis. Leipzig, 1885. [Faksimile 9]](http://www.deutschestextarchiv.de/ebbinghaus_gedaechtnis_1885/9)*

## Zitat als Epigraph mit Nennung des Urhebers (beispielhaft):

```
<epigraph>
  <cit>
    <quote>[Zitattext]</quote>
    <bibl>[Urheber des Zitats]</bibl>
  </cit>
</epigraph>
```

## Zitat als Epigraph mit Nennung des Urhebers

![](img/J35mYDmL83.png)

```
<epigraph>
  <cit>
    <quote>Süſses Leben! Schöne freundliche Gewohnheit<lb/>
des Daſeyns und Wirkens! — von dir<lb/>
ſoll ich ſcheiden?</quote>
    <lb/>
    <bibl><hi rendition="#k">Göthe</hi>,</bibl>
  </cit>
</epigraph><lb/>
```

*Quelle: [Hufeland, Christoph Wilhelm: Die
Kunst das menschliche Leben zu verlängern. Jena, 1797.
[Faksimile 7]](http://www.deutschestextarchiv.de/hufeland_leben_1797/7)*


---

## Äußeres Erscheinungsbild des zugrundeliegenden Bandes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/erschBildBand.html](https://www.deutschestextarchiv.de/doku/basisformat/erschBildBand.html)

# Äußeres Erscheinungsbild des zugrundeliegenden Bandes

## Themen

* [Seitenzahlen und Faksimilenummern](seitenFacsNr.html)
* [Orientierungshilfen im Buchblock](orientierungshilfen.html)


---

## Äußeres Erscheinungsbild des Textes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/erschBildText.html](https://www.deutschestextarchiv.de/doku/basisformat/erschBildText.html)

# Äußeres Erscheinungsbild des Textes

## Themen

* [Spalten](spalte.html)
* [Absätze](absatz.html)
* [Zeilenumbrüche](zeilenumbruch.html)
* [Horizontale Trennlinien](horizontaleLinie.html)
* [Listen](liste.html)
* [Tabellen](tabelle.html)
* [Abbildungen](abbildung.html)
* [Formeln](formeln.html)
* [Typographische Besonderheiten](typographie.html)
* [Klammerungen](klammerung.html)
* [Klammerungen](leerraum.html)
* [Schwer- und Unleserliches](gapSupplied.html)


---

## Fettdruck

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fettdruck.html](https://www.deutschestextarchiv.de/doku/basisformat/fettdruck.html)

# Fettdruck

## Kodierung von fett gedrucktem Text

![](img/gkVUOa8TFw.png)

```
Stichwörter: <hi rendition="#b"><hi rendition="#fr">Jahrhundert</hi></hi>
```

*Quelle: [Sanders, Daniel: Aus der Werkstatt eines
Wörterbuchschreibers. Plaudereien. Berlin, 1889. [Faksimile 65]](http://www.deutschestextarchiv.de/sanders_woerterbuchschreiber_1889/65)*


---

## Fortlaufende Fußnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fnFortlaufend.html](https://www.deutschestextarchiv.de/doku/basisformat/fnFortlaufend.html)

# Fortlaufende Fußnoten

Reicht eine Fußnote über einen Seitenumbruch hinaus, so wird vor dem
Seitenumbruch das `<note>`-Element geschlossen. Die
Fortsetzung der Fußnote wird dort realisiert, wo sie tatsächlich steht
(i.d.R. am Schluss der Folgeseite). Die Verbindung zwischen den Teilen der
Fußnote wird durch die Attribute `@xml:id`,
`@next` und `@prev` hergestellt:

```
<note place="foot" n="[Fußnotenreferenz]" xml:id="[ID 01]" next="#[ID 02]">[Fußnotentext]</note><lb/>
<pb facs="[Bildnummer]" n="[Seitenzahl]">
[Text Folgeseite bis Schluss]
<note place="foot" n="[Fußnotenreferenz_wie_oben]" xml:id="[ID 02]" prev="#[ID 01]">
  [Fortführung Fußnotentext]
</note><lb/>
```

## Kodierung fortlaufender Fußnoten

![](img/ffn01.png)

```
<p>
  [...] zu Entdeckungen ſolcher Art zu ge-<lb/>langen 
  <note place="foot"n="*)" xml:id="seg2pn_2_1 "next="#seg2pn_2_2">
    Huygens, der ſelbſt zur Vollendung dieſer Entdeckung ſehr we-<lb/>
    ſentlich beigetragen hat, erklärt ſich darüber in ſeiner Dioptrik<lb/>
    [...]
  </note>. Nach Borelli's Erzählung [...]
</p><lb/>
```

![](img/ffn02.png)

```
<p>
[...] können, daß Zeit und Glück auch erſt einen ſpäten Enkel begün-<lb/>
  <note xml:id="seg2pn_2_2"prev="#seg2pn_2_1"place="foot"n="*)">
    ein höheres, über alle Sterblichen weit erhabenes Weſen zu<lb/>
    halten. Aber davon ſind wir ſo weit entfernt, daß ſelbſt noch<lb/>
    [...]
    richtig zu erklären.
  </note><lb/>
  [...]
</p>
```

*Quelle: [Littrow, Joseph Johann von: Die Wunder des Himmels, oder gemeinfaßliche Darstellung des Weltsystems. Bd. 3. Stuttgart, 1836. [Faksimile 270/271].](http://www.deutschestextarchiv.de/16789/27)*

Tipp:

Zur Verknüpfung diskontinuierlicher Textbestandteile mittels der
Attribute `@xml:id`, `@next` und
`@prev` s. Kap. [Unterbrechungen zusammenhängender Textbestandteile](diskontTextpassagen.html).

HINWEIS:

***Abweichung Phase 1:** Fußnoten, die über einen Seitenumbruch hinausreichen, werden mittels des
`<seg>`-Elementes ausgezeichnet. Dabei wird vor dem
Seitenumbruch das `<note>`-Element geschlossen. Die
Fortsetzung der Fußnote wird dort realisiert, wo sie tatsächlich steht
(i.d.R. am Schluss der Folgeseite). Die Verbindung zwischen den Teilen der
Fußnote wird durch das `<seg>`-Element ausgedrückt.
An welcher Stelle im Verhältnis zueinander sich die zusammengehörigen
`<seg>`-Elemente befinden, wird durch das Attribut
`@part` ausgedrückt, das die Werte `I`
(initial), `M` (medial) und `F` (final)
annehmen kann.*


---

## Mehrfach referenzierte Fußnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fnMehrfachReferenziert.html](https://www.deutschestextarchiv.de/doku/basisformat/fnMehrfachReferenziert.html)

# Mehrfach referenzierte Fußnoten

Wird eine Fußnote mehrfach in einen Text eingewiesen, so
steht der Fußnotentext an der Stelle der ersten
Fußnotenreferenz im Fließtext. Das zugehörige
`<note>`-Element erhält
eine `@xml:id`. Weitere Referenzen auf
diese Fußnote werden innerhalb eigener
`<note>`-Elemente
wiedergegeben, die jedoch leer bleiben, d.h. der
Fußnotentext wird hier nicht wiederholt. Mittels eines
`@sameAs`-Attributs wird von den
folgenden `<note>`-Elementen auf
die `@xml:id` des
`<note>`-Elements
verwiesen, welches den Fußnotentext enthält.

```
<p>
  [Text]
    <note place="foot" n="[Fußnotenreferenz x]" xml:id="[ID-Fußnote]">
      [Fußnotentext]
    </note>
  [weiterer Text.]</p>
<p>
  [weiterer Text]
    <note place="foot" n="[Fußnotenreferenz x]" sameAs="#[ID-Fußnote]"/>
  [weiterer Text].
</p>
```

## Kodierung mehrfach referenzierter Fußnoten

![](img/xrcJtWOcqu.png)

```
<p>[...]<hi rendition="#fr">machte das Buch zu, und fieng ſeine Pre-<lb/>
  digt an</hi>
    <note xml:id="note-0058" place="foot" n="*)">
      <hi rendition="#fr">Froez</hi> iſt indeſſen ein Mann, der doch mit unter<lb/>
      gute Nachrichten giebt. [...]
    </note>.
  Wir finden gegen dieſe letzte Er-<lb/>
  za&#x0364;hlung nichts einzuwenden. Wenn aber der<lb/>
  Pater die Anmuth und Beredſamkeit, [...] 
  ſo ſehr herausſtreicht; ſo iſt er entweder<lb/>
  ſelbſt ein Budſoiſt, oder er muß nicht gewußt<lb/>
  haben, was Anmuth, u&#x0364;berzeugende und ru&#x0364;hrende<lb/>
  Beredſamkeit ſey
    <note sameAs="#note-0058" xml:id="note-0058a" place="foot" n="*)"/>
.</p><lb/>
```

*Quelle: [[Poppe, Johann Friedrich]: Characteristik der merkwürdigsten Asiatischen Nationen. Bd. 2. Breslau, 1777. [Faksimile 58]](http://www.deutschestextarchiv.de/poppe_charakteristik02_1777/58)*


---

## Auf eine Seite begrenzte Fußnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fnSeite.html](https://www.deutschestextarchiv.de/doku/basisformat/fnSeite.html)

# Auf eine Seite begrenzte Fußnoten

Fußnoten werden direkt an die Stelle im laufenden
Text gesetzt, von der aus sie referenziert
werden. Sie werden ausgezeichnet mittels:

```
<note place="foot" n="[Fußnotenreferenz]">[Fußnotentext]</note>
```

Das referenzierende Zeichen wird textgetreu
wiedergegeben; besondere Formatierungen
(Hoch-/Tiefstellung, gesperrter Druck …)
bleiben dabei unberücksichtigt.

Innerhalb des Fußnotentextes werden Formatierungen,
Spalten- und Zeilenumbrüche wie im Haupttext
gehandhabt.

## Kodierung von Fußnoten

![](img/KnjT6kNMou.png)
![](img/aGyUjtR_RE.png)

```
<p>[...]<lb/>
  — Nestorianische Gemeinden scheinen damals über weite Strecken<lb/>
  des nord-östlichen Asien verbreitet gewesen zu sein 
    <note place="foot" n="2)">
      Nach einer Inschrift in syrischer Sprache, welche Jesuiten-Missionare 1625 in<lb/>
      einer der grössten Städte der Provinz <hi rendition="#k">Šen-si</hi> fanden, 
        wäre die Einwanderung nesto-<lb/>
      rianischer Christen in das Jahr 635 zu setzen.
    </note>. Der Mönch<lb/>
  [...]
</p><lb/>
```

*Quelle: [[Berg, Albert]: Die preussische Expedition nach
Ost-Asien. Bd. 3. Berlin, 1873. [Faksimile 27]](http://www.deutschestextarchiv.de/berg_ostasien03_1873/27)*


---

## Formeln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/formeln.html](https://www.deutschestextarchiv.de/doku/basisformat/formeln.html)

# Formeln

## Themen

* [Formeln Grundstruktur](formelnAllg.html)
* [Fehlerhafte Formeln](formelnFehlerhaft.html)


---

## Grundstruktur der Kodierung von Formeln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/formelnAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/formelnAllg.html)

# Grundstruktur der Kodierung von Formeln

Formeln werden zunächst mit einem leeren `<formula/>`-Element
gekennzeichnet. In einem zweiten Erfassungsschritt können die Formeln entsprechend der
TeX-Notation transkribiert und mittels `<formula>[...]</formula>`
umschlossen werden. Das `<formula>`-Element erhält dabei ein Attribut
`@notation`, in welchem die Notation (`"TeX"` oder
`"MathML"`) angegeben wird. In einem weiteren Attribut `@facs`
kann auf eine graphische Darstellung der betreffenden Formel verwiesen werden.

Zu den Formeln zählen:

* mathematische und physikalische Formeln und Gleichungen,
* Brüche (mit Bruchstrich; sofern nicht als Unicode-Entität vorhanden),
* chemische Verbindungen,
* Ausdrücke der Logik.

Reine Variablen werden nicht als `<formula>` kodiert.

Formeln können sowohl innerhalb einer Zeile (inline) als auch abgesetzt vom Fließtext
stehen. In letzterem Fall wird der Zeilenumbruch vor und nach der Formel mittels
`<lb/>` angegeben. Steht unmittelbar nach einer Formel ein Satzzeichen,
wird dieses mit erfasst. Layout-Informationen (z.B. Zentrierung) bleiben unberücksichtigt.

## Kodierung von Formeln (1)

![](img/S_y8v_2j1c.png)

```
<formula notation="TeX">
  \lambda_T = \frac{1}{\pi ns^2}\int\limits_0^\infty\frac{4x^2e^{-x^2}dx}{\psi(x)+\frac{n_1\sigma^2}{ns^2}\psi\left(x\sqrt\frac{m_1}{m}\right)}
</formula>
```

*Quelle: [Boltzmann, Ludwig: Vorlesungen über Gastheorie. Bd. 1.
Leipzig, 1896. [Faksimile 87]](http://www.deutschestextarchiv.de/boltzmann_gastheorie01_1896/87)*

## Kodierung von Formeln (2)

![](img/x6hBcfT91w.png)

```
<formula notation="TeX">
  U=u_1 \, \left ( \frac{z_1}{z_2} \cdot \frac{z_3}{z_4} - 1 \right )
</formula>
```

*Quelle: [Fischer, Hermann: Die Werkzeugmaschinen. Bd. 1: Die
Metallbearbeitungs-Maschinen. [Textband]. Berlin, 1900. [Faksimile 181]](http://www.deutschestextarchiv.de/fischer_werkzeugmaschinen01_1900/181)*

## Kodierung von Formeln (3)

![](img/yeiZqiWbkM.png)

```
<p>Wir setzen wieder<lb/>
  <formula notation="TeX">\frac{\cos kr}{r} = f_r + \frac{1}{r}</formula>,<lb/>
  <formula notation="TeX">\Psi = \Psi' + \Psi''</formula>,<lb/>
  <formula notation="TeX">\Psi' = \int pf_rd\omega</formula>,<lb/>
  <formula notation="TeX">\Psi'' = \int p\frac{1}{r}d\omega</formula>.
</p><lb/>
```

*Quelle: [Helmholtz, Hermann von: Theorie der Luftschwingungen in
Röhren mit offenen Enden. In: Journal für die reine und angewandte Mathematik 57
(1860), Heft 1, S. 1-72. [Faksimile 31]](http://www.deutschestextarchiv.de/helmholtz_luftschwingungen_1860/31)*


---

## Umgang mit fehlerhaften Formeln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/formelnFehlerhaft.html](https://www.deutschestextarchiv.de/doku/basisformat/formelnFehlerhaft.html)

# Umgang mit fehlerhaften Formeln

Druckfehler in Formeln werden mittels des `<choice>`-Elements
wiedergegeben. Dabei steht die Formel jeweils in Gänze im `<sic>`-Element
(fehlerhaftes Original) bzw. im `<corr>`-Element (korrigierte
Transkription).

```
<choice>
  <sic><formula notation="[Notation]">[fehlerhafte Formel entsprechend der Vorlage]</formula></sic>
  <corr><formula notation="[Notation]">[korrigierte Transkription der Formel]</formula></corr>
</choice>
```

## Umgang mit fehlerhaften Formeln

![](img/Aj_3_pYrix.png)

```
<choice>
  <sic>
    <formula notation="TeX">\frac{3 \cdot 015}{3 - 0{,}15}</formula>
  </sic>
  <corr>
    <formula notation="TeX">\frac{3 \cdot 0{,}15}{3 - 0{,}15}</formula>
  </corr>
</choice>
```

*Quelle: [Siemens, Werner von: Gesammelte Abhandlungen und
Vorträge. Berlin, 1881. [Faksimile 208]](http://www.deutschestextarchiv.de/siemens_abhandlungen_1881/208)*


---

## Frakturwechsel

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/frakturwechsel.html](https://www.deutschestextarchiv.de/doku/basisformat/frakturwechsel.html)

# Frakturwechsel

## Kodierung des Wechsels der Frakturschrift

![](img/TOe1MVF1Vd.png)

```
<p>
  <hi rendition="#fr">Eine Madonna mit dem Kinde.</hi> Sie<lb/>
  haͤlt ein Buch. [...]
</p><lb/>
```

*Quelle: [Ramdohr, Friedrich Wilhelm Basilius von: Über
Mahlerei und Bildhauerarbeit in Rom für Liebhaber des Schönen in der Kunst. T.
2. Leipzig, 1787. [Faksimile 86]](http://www.deutschestextarchiv.de/ramdohr_mahlerei02_1787/86)*

Der Wechsel zwischen zwei Frakturschriften wird nur im Fließtext beachtet. Auf
Titelblättern, in Überschriften o. ä. wird der Frakturwechsel nicht vermerkt.


---

## Fremdsprachliches Material

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fremdsprachlMaterial.html](https://www.deutschestextarchiv.de/doku/basisformat/fremdsprachlMaterial.html)

# Fremdsprachliches Material

Fremdsprachliche Passagen werden grundsätzlich mit erfasst, müssen
jedoch nicht gesondert als solche gekennzeichnet werden (DTABf –
Level 2).

Soll eine Kennzeichnung fremdsprachlichen Materials als solches
erfolgen (DTABf – Level 3), so ist dies im Element
`<foreign>` möglich. Die Angabe der
betreffenden Sprache ist obligatorisch und erfolgt im Attribut
`@xml:lang` als dreibuchstabiger Code entsprechend
der [ISO-Norm 639-3](http://www-01.sil.org/iso639-3/codes.asp).

```
<foreign xml:lang="[ISO 639-3 Code]">[fremdsprachliche Textpassage]</foreign>
```

Ist die Sprache einer fremdsprachlichen Textpassage nicht
definierbar, so steht in `@xml:lang` der Wert "und"
(i.e. "undefiniert").

In `@xml:lang` wird grundsätzlich genau eine Sprache
angegeben. Die Verschachtelung von
`<foreign>`-Elementen zur Kennzeichnung
mehrerer Sprachen für eine fremdsprachliche Passage ist zu
vermeiden. Gelten für eine fremdsprachliche Passage mehrere
Sprachen, so wird dies mit dem Wert `"mul"`
ausgedrückt. Eine nähere Spezifikation der Sprachen erfolgt nicht in
`@xml:lang`. (Raum für diese Angabe bietet jedoch der
editorische Kommentar; vgl. Kap. [Editorischer Sachkommentar](editorEingriff.html).)

## Kodierung von fremdsprachlichem Material

![](img/laLcGRzsUZ.png)

```
<p>[...] sanskr. iran. griech. umbr. osk. 
  <hi rendition="#i"><foreign xml:lang="mul">an</foreign></hi> , aber lat. 
  <hi rendition="#i"><foreign xml:lang="lat">in</foreign></hi> , deutsch 
  <hi rendition="#i">un</hi> .<lb/>[...]
</p>
```

*Quelle: [Curtius, Georg: Zur Kritik der
neuesten Sprachforschung. Leipzig, 1885. [Faksimile
101]](http://www.deutschestextarchiv.de/curtius_sprachforschung_1885/101)*

Besteht der gesamte Inhalt eines strukturierenden Elements aus
fremdsprachlichem Material, so kann dies innerhalb des jeweiligen
strukturierenden Elements durch das Attribut
`@xml:lang` angezeigt werden.

## Umgang mit gänzlich fremdsprachlichem Elementinhalt

![](img/zJwO_722Nd.png)

```
<titlePage>
  [...] 
  <epigraph>
    <cit>
      <quote xml:lang="fra">
        <hi rendition="#aq">Tel eſt l'effet de la vérité: on la repouſſe; mais<lb/>
        en la repouſſant on la voit, & elle pénètre.</hi>
      </quote><lb/>
      <bibl>
        <hi rendition="#et #aq"><hi rendition="#i">Garat le jeune</hi>.</hi>
      </bibl>
    </cit>
  </epigraph>[...]
</titlePage><lb/>
```

*Quelle: [Jacobi, Friedrich Heinrich:
Eduard Allwills Briefsammlung. Mit einer Zugabe von eigenen
Briefen. Königsberg, 1792. [Faksimile 9]](http://www.deutschestextarchiv.de/jacobi_allwill_1792/9)*

Fremdsprachliches Textmaterial, das nicht entzifferbar ist oder aus
anderen Gründen (zunächst) nicht transkribiert wird, wird mittels
des oben beschriebenen `<foreign>`-Elements
angedeutet. Auf die fehlende Transkription weist ein
`<gap/>`-Element mit dem Hinweis
`@reason="fm"` hin (siehe auch Kap. [Unleserliche bzw.
schwer entzifferbare Zeichen](gapSupplied.html)).

```
<foreign xml:lang="[ISO 639-3 Code]">
  <gap reason="fm"/>
</foreign>
```

## Umgang mit nicht entzifferbarem fremdsprachlichem Material

![](img/GgVFes0JvV.png)

```
<p> [...] Plagen/ 
    <foreign xml:lang="ell"><gap reason="fm"/></foreign> 
  Gesetzt aber/ [...]
</p><lb/>
```

*Quelle: [Breymann, Conrad Andreas: Die
Vertreibung der Bitterkeit des Todes/ Welche bey dem
Hochansehnlichen Leich-Begängniß/ So auf Hohe Verordnung Sr.
Hoch-Fürstl. Durchl. ... Dem ... Herrn Eberhard Finen/ ... Als
Derselbe Den 12ten Apr. des 1726ten Jahrs ... entschlafen/ ...
vorgestellet ... Blanckenburg, 1727. [Faksimile
11]](http://www.deutschestextarchiv.de/breymann_vertreibung_1727/11)*


---

## Einleitende Informationen zum Buch

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/front.html](https://www.deutschestextarchiv.de/doku/basisformat/front.html)

# Einleitende Informationen zum Buch

## Themen

* [Einleitende Buchteile Grundstruktur](frontAllg.html)
* [Titelblatt](titelblatt.html)
* [Widmungen](widmung.html)
* [Epigraphe](epigraph.html)
* [Inhaltsverzeichnis](inhaltsverzeichnis.html)


---

## Grundstruktur der Kodierung einleitender Buchteile

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/frontAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/frontAllg.html)

# Grundstruktur der Kodierung einleitender Buchteile

Die einleitenden Teile eines Buches (die Titelei mit Schmutztitel,
Frontispiz, Titelblatt, Impressum etc., das Inhaltsverzeichnis, das
Vorwort, Widmungen) werden mit dem
`<front>`-Element umschlossen. Folgende Elemente
können im `<front>`-Element enthalten sein:

* `<div>` (Textpassage einer bestimmten
  Textsorte): innerhalb von `<front>` mit den
  möglichen `@type`-Werten
  + `dedication` (Widmung),
  + `frontispiece` (Frontispiz),
  + `copyright` (Hinweise zum Copyright),
  + `contents` (Inhaltsverzeichnis),
  + `imprimatur` (Druckerlaubnis),
  + `imprint` (Angaben zur Publikation),
  + `preface` (Geleitwort, Vorwort,
    Einleitung)
* `<titlePage>` (Titelseite)
* `<epigraph>` (Zitat): auch in anderen Kontexten
  möglich; s. dazu Kap. [Zitate und Epigraphe](zitateEpigraphe.html)
* `<figure>` (Abbildung): auch in anderen
  Kontexten möglich; s. dazu Kap. [Abbildungen](abbildung.html)
* `<advertisement>` (Anzeige): auch in anderen
  Kontexten möglich; s. dazu Kap. [Anhang](anhang.html)

Anmerkung:

Sowohl für das Geleitwort als auch für das Vorwort und die
Einleitung eines Buches wird `@type="preface"` als
Spezifikation des `<div>`-Elements gesetzt. Somit
erfolgt im Tagging keine Unterscheidung zwischen diesen Textsorten bzw.
den (möglicherweise unterschiedlichen) Autoren derselben.

Beispielhafte Strukturierung der einleitenden Teile eines Buchs:

```
<front>
  <figure/>
  <titlePage type="halftitle">[Inhalte Schmutztitelblatt]</titlePage>
  <titlePage type="main">[Inhalte Titelblatt]</titlePage>
  <div type="imprimatur">[Druckerlaubnis]</div>
  <div type="contents">[Inhaltsverzeichnis]</div>
  <div type="dedication">[Widmung]</div>
  <div type="preface">[Einleitung]</div>
</front>
```


---

## Fußnoten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/fussnote.html](https://www.deutschestextarchiv.de/doku/basisformat/fussnote.html)

# Fußnoten

* [Seitenweise Fußnoten](fnSeite.html)
* [Fortlaufende Fußnoten](fnFortlaufend.html)
* [Mehrfach referenzierte Fußnoten](fnMehrfachReferenziert.html)


---

## Schwer bzw. nicht entzifferbare Zeichen und Auslassungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/gapSupplied.html](https://www.deutschestextarchiv.de/doku/basisformat/gapSupplied.html)

# Schwer bzw. nicht entzifferbare Zeichen und Auslassungen

**Schwer leserliche Zeichen oder Zeichenketten** (z.B. durch
physische Mängel der Vorlage, schwachen Druck) werden mit dem Tag
`<supplied>` umschlossen:

```
<supplied>[Zeichen oder Zeichenkette]</supplied>
```

Ist die Lesung für die ergänzte Zeichenkette unsicher, so kann mit
einem `@cert`-Attribut im supplied-Element der Grad der Sicherheit für
die Ergänzung angezeigt werden. Der Grad der Sicherheit wird dabei wie
folgt angezeigt:

| Ausdruck | Bedeutung |
| --- | --- |
| `<supplied>` | Gewissheit/sichere Lesart (z.B. das Zeichen/die Zeichenkette ist noch schwach gedruckt, die Lesung somit gesichert) |
| `<supplied cert="high">` | hohe Sicherheit der Ergänzung (z.B. das Zeichen/die Zeichenkette ist nicht mehr erkennbar, aber die Lesung ergibt sich aus dem Kontext und ist somit gesichert) |
| `<supplied cert="low">` | niedrige Sicherheit der Ergänzung/unsichere Lesart (z.B. das Zeichen/die Zeichenkette ist nicht mehr erkennbar und wurde rekonstruiert; andere Rekonstruktionen sind daneben denkbar) |

**Lassen sich die Zeichen nicht erkennen und nicht mehr
rekonstruieren**, wird das Tag `<gap/>`
gesetzt, um die Lücke anzuzeigen. Innerhalb des
`<gap>`-Tags kann mittels der Attribute
`@unit`, `@quantity` und
`@reason` der Bezug angezeigt werden, wie viele
Zeichen die Lücke umfasst, sowie der Grund der Fehlstelle:

```
<gap unit="chars" quantity="[Anzahl der Zeichen, die fehlen]" reason="[Grund für die Fehlstelle]"/>
```

Folgende Werte kann das `@unit`-Attribut annehmen:

|  |  |
| --- | --- |
| `chars` | Zeichen |
| `lines` | Zeilen |
| `pages` | Seiten |
| `words` | Wörter |

Folgende Werte kann das `@reason`-Attribut annehmen:

|  |  |
| --- | --- |
| `lost` | Zerstörung |
| `illegible` | unleserlich |
| `fm` | fremdsprachlicher Text (foreign language material) |
| `insignificant` | als für das Korpus unwichtig eingestufter Text |

## Umgang mit Auslassungen/Lücken

![](img/BttIlQRtWe.png)

```
He<gap reason="lost" unit="chars" quantity="1"/>rde
```

*Quelle:
[Antonius Anthus [i. e. Blumröder, Gustav]: Vorlesungen über Esskunst. Leipzig, 1838. [Faksimile 53]](http://www.deutschestextarchiv.de/anthus_esskunst_1838/53)*


---

## Verknüpfung diskontinuierlicher Vers-Teile

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/geDiskontVerse.html](https://www.deutschestextarchiv.de/doku/basisformat/geDiskontVerse.html)

# Verknüpfung diskontinuierlicher Vers-Teile

Verse können aus Platzgründen in der Zeile des vorangehenden oder folgenden Verses
fortgeführt werden. Um dies darzustellen, werden die Attribute `@prev`,
`@next` und `@xml:id` eingesetzt. Zur Verwendung dieser Attribute s. Kap.
[Unterbrechungen zusammenhängender Textbestandteile](diskontTextpassagen.html).

*Fortführung eines Verses in der Zeile des nachfolgenden Verses:*

```
<l xml:id="[ID Vers 1]" next="#[ID Schluss Vers 1]">[Beginn Vers 1]</l>
<lb/>
<l>[Vers 2]</l>
<l xml:id="[ID Schluss Vers 1]" prev="#[ID Vers 1]">[Schluss Vers 1]</l>
<lb/>

```

*Fortführung eines Verses in der Zeile des vorangehenden Verses:*

```
<l>[Vers 1]</l>
<l xml:id="[ID Schluss Vers 2]" prev="#[ID Vers 2]">[Schluss Vers 2]</l>
<lb/>
<l xml:id="[ID Vers 2]" next="#[ID Schluss Vers 2]">[Vers 2]</l>
<lb/>

```

Anmerkung:

Die Attribute `@prev` und `@next` sind also
semantisch, nicht linear zu verstehen, d.h. `@next` kann
**vor** dem dazugehörigen `@prev` stehen, wenn dies den
Gegebenheiten der Vorlage entspricht.


---

## Gedichte in Gedichtbänden

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/geLyrikband.html](https://www.deutschestextarchiv.de/doku/basisformat/geLyrikband.html)

# Gedichte in Gedichtbänden

In Gedichtbänden können innerhalb von Gedichten neben dem
Gedichttitel und den einzelnen Strophen zusätzliche Textbestandteile
vorkommen, z.B. Datumszeilen, Sprecher oder zusätzliche Angaben zur
Entstehungsgeschichte des Gedichts. In Gedichtbänden mit solcherlei
Gedichten ebenso wie in literarischen Sammlungen verschiedener
Textsorten wird die Grundstrukturierung mittels
`<div>`-Elementen vorgenommen. Ein Gedicht wird
dabei durch ein `<div>`-Element umschlossen;
der Gedichttitel steht im `<head>` des
umschließenden `<div>`-Elements. Datumszeilen,
Sprecher, zusätzliche Angaben in einfacher Prosa werden wie gewohnt
ausgezeichnet. Die Gedichtauszeichnung mittels
`<lg>`s beginnt auf Strophenebene.

Auszeichnung von Gedichten in Gedichtbänden (beispielhaft):

```
<div type="poem">
  <head>[Titel]</head><!-- sofern vorhanden -->
  <dateline>[Datumsangabe]</dateline>
  <lg type="poem">
    <lg n="[Strophennummer]"><!-- sofern kein einstrophiges Gedicht -->
      <l>[Vers]</l>
      <l>[Vers]</l>
    </lg>
  </lg>
</div>
```

## Kodierung von Gedichten in Gedichtbänden

![](img/9ZqgQkldRA.png)

```
<div type="poem">
  <head rendition="#g">An<lb/><hi rendition="#b">den Apoll,<lb/>
    daß er die Leyer zuruͤcknehmen moͤchte.</hi>
  </head><lb/>
  <p rendition="#c">
    [Als ſie zu Berlin wegen Mangel an Quartieren einige<lb/>Zeitlang in einer Dachſtube wohnen mußte.]
  </p><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <dateline rendition="#c">1763.</dateline><lb/>
  <lg type="poem">
    <lg n="1">
      <l><hi rendition="#in">A</hi>poll! nimm deine Leyer wieder,</l><lb/>
      <l>Des Flakkus Toͤne fehlen ihr,</l><lb/>
      <l>Er ſang im dunklen Walde Lieder</l><lb/>
      <l>Und vor ihm ſtaunete das Thier.</l>
    </lg>
    [...]
  </lg><lb/>
  [...]
</div><lb/>
```

*Quelle: [Karsch, Anna Luise: Gedichte.
Berlin, 1792. [Faksimile 188]](http://www.deutschestextarchiv.de/karsch_gedichte_1792/188)*


---

## Gedichte in Prosawerken

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/geProsa.html](https://www.deutschestextarchiv.de/doku/basisformat/geProsa.html)

# Gedichte in Prosawerken

Gedichte in Prosawerken und Gedichtbänden mit einfacher Struktur
(d.h. nur Gedichttitel und Strophen, keine zusätzlichen
Textbestandteile) werden mittels `<lg>`s
strukturiert. Dabei umschließt das Element
`<lg>` zum einen das gesamte Gedicht, wobei
diese Verwendung durch das Attribut-Wert-Paar
`@type="poem"` angezeigt wird. Das
`<lg>`-Element umschließt weiterhin jede
einzelne Strophe. In diesem Fall steht kein
`@type`-Attribut. Bei mehrstrophigen Gedichten wird
die jeweilige Strophennummer im `@n`-Attribut des
`<lg>`-Elements angegeben. Der Gedichttitel
steht im `<head>`-Element der äußeren
`<lg>`. Verse werden innerhalb der
`<lg>` mittels
`<l>[...]</l>` ausgezeichnet. Ein Vers
kann dabei über einen Zeilenumbruch hinausreichen.

```
<lg type="poem">
  <head>[Titel]</head><lb/> <!-- sofern vorhanden -->
  <lg n="[Strophennummer]"> <!-- sofern kein einstrophiges Gedicht -->
    <l>[Vers]</l><lb/>
    <l>[Vers]</l><lb/>
  </lg>
</lg>
```

## Kodierung von Gedichten in Prosawerken

![](img/o2JSxkY8WB.png)

```
<p>
  Möchte das Lied vom <hi rendition="#g">deutſchen</hi> Helgoland, das Karl<lb/>
  Tannen in Bremen bereits vor zwölf Jahren ſang, überall in<lb/>
  ganz Deutſchland erklingen und jeden Deutſchen daran erinnern,<lb/>
  daß die Inſel ein verlorenes Kind unſerer Mutter Germania<lb/>
  iſt, welches wir zurückfordern müſſen und wollen.
</p><lb/>
<lg type="poem">
  <lg n="1">
    <l>Im Meer, im herrlich deutſchen Meer</l><lb/>
    <l>Klagt Wind und Woge laut und ſchwer,</l><lb/>
    <l>Und jede Welle trägt es fort</l><lb/>
    <l>Von dem verlor’nen Kind das Wort</l><lb/>
    <l>Roth is de Kant,</l><lb/>
    <l>Witt is dat Sand,</l><lb/>
    <l>Das iſt das <hi rendition="#g">deutſche</hi> Helgoland!</l>
  </lg><lb/>
  <lg n="2">
    <l>Germania, du Mutter mein!</l><lb/>
    <l>Du ſammelſt deine Glieder ein;</l><lb/>
    <l>Vergiß auch nicht dein kleinſtes Kind,</l><lb/>
    <l>Umbrauſt von Wogendrang und Wind.</l><lb/>
    <l>Roth is de Kant,</l><lb/>
    <l>Witt is dat Sand,</l><lb/>
    <l>Das iſt das <hi rendition="#g">deutſche</hi> Helgoland!</l>
  </lg>
</lg><lb/>
```

*Quelle: [Werner, Reinhold von:
Erinnerungen und Bilder aus dem Seeleben. Berlin, 1880.
[Faksimile 214]](http://www.deutschestextarchiv.de/werner_seeleben_1880/214)*


---

## Gedichte und gebundene Sprache

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/gedichte.html](https://www.deutschestextarchiv.de/doku/basisformat/gedichte.html)

# Gedichte und gebundene Sprache

## Themen

* [Gedichte in Prosawerken](geProsa.html)
* [Gedichte in Gedichtbänden](geLyrikband.html)
* [Diskontinuierliche Vers-Teile](geDiskontVerse.html)


---

## Grundstruktur jedes TEI-Dokuments

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/grundstrukturDokument.html](https://www.deutschestextarchiv.de/doku/basisformat/grundstrukturDokument.html)

# Grundstruktur jedes TEI-Dokuments

Das Wurzelelement jedes TEI-Dokuments im DTA bildet das `<TEI>`-Element,
dessen `@xmlns`-Attribut den TEI-Namensraum (namespace) spezifizieren,
der für das jeweilige Dokument gilt:

```
<TEI xmlns="http://www.tei-c.org/ns/1.0">...</TEI>
```

Jedes TEI-Dokument im DTA besteht aus einem Header, der Metadaten zum
publizierten Text umfasst, und einem Textbereich, der alle Transkriptionen
mit den zugehörigen Annotationen enthält. Dieser Volltext umfasst dabei nicht
allein den eigentlichen Buchtext, sondern alle Textbestandteile, so auch
Titelseite und Vorwort sowie in der Regel die Register, Beigaben und Anhänge.

Die folgende Struktur wird in jedem TEI-Dokument eingehalten:

```
<teiHeader>[Metadaten]</teiHeader>
<text>
  <front>[Elemente vor Beginn des Buchtextes]</front>
  <body>[Textkörper]</body>
  <back>[Elemente nach Abschluss des Buchtextes]</back>
</text>
```


---

## Haupttitelseite

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/haupttitel.html](https://www.deutschestextarchiv.de/doku/basisformat/haupttitel.html)

# Haupttitelseite

## Kodierung von Titelblättern bei Monographien – Haupttitelseite

![](img/XyxkvQl3Zk.png)

```
<titlePage type="main">
  <docTitle>
    <titlePart type="main">
      <hi rendition="#g"><hi rendition="#b">Vorleſungen</hi><lb/>
      u&#x0364;ber<lb/><hi rendition="#b">Esskunst</hi></hi>
    </titlePart>
  </docTitle><lb/>
  <byline>
    <hi rendition="#g">von</hi><lb/>
    <docAuthor><hi rendition="#g #b">Antonius Anthus.</hi></docAuthor>
  </byline><lb/>
  <epigraph>
    <cit>
      <quote>„Ernſt iſt das Leben, heiter iſt die Kunſt.“</quote>
    </cit>
  </epigraph><lb/>
  <figure/><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <docImprint>
    <pubPlace><hi rendition="#g #b">Leipzig,</hi></pubPlace><lb/>
    <publisher>
      <hi rendition="#g">Verlag von Otto Wigand.</hi>
    </publisher><lb/>
    <milestone rendition="#hr" unit="section"/><lb/>
    <docDate>
      <hi rendition="#b"><hi rendition="#g">1838</hi>.</hi>
    </docDate>
  </docImprint><lb/>
</titlePage>
```

*Quelle:  [Antonius
Anthus [i. e. Blumröder, Gustav]:
Vorlesungen über Esskunst. Leipzig,
1838. [Faksimile 7]](http://www.deutschestextarchiv.de/anthus_esskunst_1838/7)*


---

## Hilfreiche Tools und Anwendungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/hilfreicheTools.html](https://www.deutschestextarchiv.de/doku/basisformat/hilfreicheTools.html)

# Hilfreiche Tools und Anwendungen

Zur Unterstützung der DTABf-konformen Erfassung von Metadaten und
Textdaten stellt das DTA spezielle Anwendungen bereit.

## Webformular zur DTABf-konformen Aufnahme von Metadaten

Das DTA stellt ein Webformular bereit, welches
die Erstellung DTABf-konformer TEI-Header unterstützt. Nutzer müssen
somit die komplexe TEI-Header-Struktur nicht selbst produzieren,
sondern können Metadaten bequem über das Webformular erfassen und
daraus automatisiert einen DTABf-konformen TEI-Header erstellen
lassen.

➔ Zum [Webformular für die Metadatenerfassung](http://www.deutschestextarchiv.de/dtae/submit/clarin)

[![](img/webformular.png)](http://www.deutschestextarchiv.de/dtae/submit/clarin)

Screenshot des Webformlars für die Metadatenerfassung

## oXygen-Framework zur Texterfassung und Annotation

Für die Texterfassung und DTABf-konforme
Annotation bietet das DTA ein Framework für den Autormodus des
oXygen-XML-Editors an. Das DTA-oXygen-Framework DTAoX ermöglicht
eine ad hoc Visualisierung der TEI/XML-annotierten Texte. Darüber
hinaus ist es mit DTAoX möglich, die Texterfassung und Annotation
von vornherein in einer WYSIWYG-Umgebung vorzunehmen. DTAoX ist
unter der GNU Lesser General Public License (LGPL) verfügbar. Die
aktuelle Version wurde für die Versionen 14.2 und 15 des [oXygen-XML-Editors](http://www.oxygenxml.com/) getestet.

➔ Zum Download: *Version 1.1.1 (29.11.2013):*
[Framework](http://www.deutschestextarchiv.de/files/DTAoX-1.1.1.zip) (.zip)

![](img/dtaox.png)

Screenshot des DTA-oXygen-Frameworks


---

## Hochstellung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/hochstellung.html](https://www.deutschestextarchiv.de/doku/basisformat/hochstellung.html)

# Hochstellung

## Kodierung von hochgestellten Zeichen (1)

![](img/IXTaTDURQx.png)

```
das Ventil <hi rendition="#i">R</hi><hi rendition="#sup">2</hi>
```

*Quelle: [Beck, Ludwig: Die Geschichte des Eisens. Bd. 2:
Das XVI. und XVII. Jahrhundert. Braunschweig, 1895. [Faksimile 955]](http://www.deutschestextarchiv.de/beck_eisen02_1895/955)*

## Kodierung von hochgestellten Zeichen (2)

![](img/7eRz9lHCLn.png)

```
in dem Gefäſs <hi rendition="#i">P</hi><hi rendition="#sup">1</hi>
```

*Quelle: [Beck, Ludwig: Die Geschichte des Eisens. Bd. 2:
Das XVI. und XVII. Jahrhundert. Braunschweig, 1895. [Faksimile 955]](http://www.deutschestextarchiv.de/beck_eisen02_1895/955)*


---

## Horizontale Trennlinien

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/horizontaleLinie.html](https://www.deutschestextarchiv.de/doku/basisformat/horizontaleLinie.html)

# Horizontale Trennlinien

Auf horizontale Trennlinien oder verzierte Trennelemente zwischen Textpassagen wird
mittels des `<milestone>`-Elements hingewiesen:

```
<milestone unit="section" rendition="#hr"/><lb/>
```

Berücksichtigt werden dabei allein Trennelemente zwischen Textpassagen oder am Ende
eines Abschnitts. Trennlinien zwischen dem Text und dem Fußnotenbereich/der Kopfzeile
bleiben hingegen unberücksichtigt.

## Kodierung von horizontalen Trennlinien

![](img/ftVsBchW7h.png)

```
<div n="1"> 
  <head> <hi rendition="#b"><hi rendition="#g">Vorwort</hi>.</hi> </head><lb/> 
  <milestone rendition="#hr" unit="section"/><lb/>
  <p>„<hi rendition="#in">E</hi>rſt die Fremde lehrt uns, 
    was wir an der Heimath be-<lb/> ſitzen.“ [...]
  </p><lb/>
</div>
```

*Quelle:
[Fontane,
Theodor: Wanderungen durch die Mark Brandenburg. [Bd. 1: Die Grafschaft
Ruppin. Der Barnim. Der Teltow]. Berlin, 1862. [Faksimile 11]](http://www.deutschestextarchiv.de/fontane_brandenburg01_1862/11)*

Eine Einfärbung der Linien bzw. Trennelemente kann durch die Verwendung der
Attribut-Wert-Kombination `@rendition="#hrBlue"` bzw.
`@rendition="#hrRed"` kodiert werden.


---

## Hilfen zur Benutzung des DTA-Basisformats

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/howto.html](https://www.deutschestextarchiv.de/doku/basisformat/howto.html)

# Hilfen zur Benutzung des DTA-Basisformats

Das folgende Kapitel bietet eine Einführung in die Nutzung des DTABf-Schemas, der DTABf-Dokumentation
sowie hilfreicher Tools und Anwendungen.

## Themen

* [Nutzung des DTA-Basisformat-Schemas](benutzungDTABfSchema.html)
* [Nutzung der DTABf-Dokumentation](zurDokumentation.html)
* [Hilfreiche Tools und Anwendungen](hilfreicheTools.html)
* [Grundstruktur jedes TEI-Dokuments](grundstrukturDokument.html)


---

## Impressum

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/impressum](https://www.deutschestextarchiv.de/doku/basisformat/impressum)

# Impressum

Impressum, Nutzungsbedingungen, Kontaktdaten sowie Hinweise zum Datenschutz

## Herausgeber

Das DTA-Basisformat wurde im Rahmen des Projekts [Deutsches Textarchiv](http://www.deutschestextarchiv.de) erarbeitet und wird
herausgegeben vom Zentrum Sprache an der
Berlin-Brandenburgischen Akademie der Wissenschaften (BBAW).

* Vertretungsberechtigter: Prof. Dr. Dr. h. c. mult. Christoph Markschies (Präsident der
  BBAW)
* Organisation: Berlin-Brandenburgische Akademie der Wissenschaften (BBAW), Jägerstraße 22/23, D-10117 Berlin, Umsatzsteuer-Identifikationsnummer: DE167449058
* Herausgeber: Zentrum Sprache der BBAW, Jägerstraße 22/23, D-10117 Berlin

## Nutzungsbedingungen

Die Komponenten des DTA-Basisformats (Dokumentation, ODDs, Schematron-Constraint-Set, RNGs)
unterliegen der Lizenz [Creative Commons: Namensnennung - Weitergabe unter gleichen Bedingungen 3.0 Deutschland (CC BY-SA 3.0 DE)](https://creativecommons.org/licenses/by-sa/3.0/de/).

Für die DTABf-annotierten Texte des Deutschen Textarchivs gelten eigene
lizenzrechtliche Bestimmungen, die in den
[Nutzungsbedingungen des DTA](http://www.deutschestextarchiv.de/doku/nutzungsbedingungen)
festgelegt sind.

## Bearbeiter und Verantwortliche

* Weiterentwicklung des Formats: [DTABf-Steuerungsgruppe](steuerungsgruppe.html) ([Matthias Boenig](https://tboenig.github.io/), [Daniel Burckhardt](https://www.ghi-dc.org/ghi-staff/research-service/daniel-burckhardt.html), [Stefan Dumont](http://www.bbaw.de/die-akademie/mitarbeiter/dumont), [Alexander Geyken](http://www.bbaw.de/die-akademie/mitarbeiter/geyken), [Martina
  Gödel](http://textloop.de/werdegang/), [Susanne Haaf](https://www.uni-leipzig.de/personenprofil/mitarbeiter/susanne-haaf-dumont), [Axel Herold](http://www.bbaw.de/die-akademie/mitarbeiter/herold), [Christian Thomas)](http://www.bbaw.de/die-akademie/mitarbeiter/thomas)
* Schema, Dokumentation & Pflege des Formats bis 2023: Susanne Haaf
* Entwicklung des Formats (bis 2017): Matthias Boenig, Alexander Geyken, Susanne Haaf, Christian Thomas, Frank Wiegand
* Vorarbeiten (bis 2010): Oliver Duntze, Christiane Fritze, Alexander Geyken

Kontakt: [redaktion@deutschestextarchiv.de](mailto:redaktion@deutschestextarchiv.de)

Das Tagset des DTA-Basisformats basiert auf den [P5-Richtlinien der Text Encoding Initiative (TEI)](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/index.html).

## Technische Realisierung der Dokumentationsseiten

Diese Dokumentation basiert auf dem XML-Dokumentationsformat
[DITA (Darwin Information Typing Architecture)](http://docs.oasis-open.org/dita/v1.2/spec/DITA1.2-spec.html).

Die mobile Webseite wurde mithilfe des
[oXygen XML Editors](https://www.oxygenxml.com/) erstellt und
an das Design des Deutschen Textarchivs angepasst.

Technische Realisierung und Anpassungen: Susanne Haaf, unter Mitarbeit von Matthias Boenig


---

## Impressum

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/impressum.html](https://www.deutschestextarchiv.de/doku/basisformat/impressum.html)

# Impressum

Impressum, Nutzungsbedingungen, Kontaktdaten sowie Hinweise zum Datenschutz

## Herausgeber

Das DTA-Basisformat wurde im Rahmen des Projekts [Deutsches Textarchiv](http://www.deutschestextarchiv.de) erarbeitet und wird
herausgegeben vom Zentrum Sprache an der
Berlin-Brandenburgischen Akademie der Wissenschaften (BBAW).

* Vertretungsberechtigter: Prof. Dr. Dr. h. c. mult. Christoph Markschies (Präsident der
  BBAW)
* Organisation: Berlin-Brandenburgische Akademie der Wissenschaften (BBAW), Jägerstraße 22/23, D-10117 Berlin, Umsatzsteuer-Identifikationsnummer: DE167449058
* Herausgeber: Zentrum Sprache der BBAW, Jägerstraße 22/23, D-10117 Berlin

## Nutzungsbedingungen

Die Komponenten des DTA-Basisformats (Dokumentation, ODDs, Schematron-Constraint-Set, RNGs)
unterliegen der Lizenz [Creative Commons: Namensnennung - Weitergabe unter gleichen Bedingungen 3.0 Deutschland (CC BY-SA 3.0 DE)](https://creativecommons.org/licenses/by-sa/3.0/de/).

Für die DTABf-annotierten Texte des Deutschen Textarchivs gelten eigene
lizenzrechtliche Bestimmungen, die in den
[Nutzungsbedingungen des DTA](http://www.deutschestextarchiv.de/doku/nutzungsbedingungen)
festgelegt sind.

## Bearbeiter und Verantwortliche

* Weiterentwicklung des Formats: [DTABf-Steuerungsgruppe](steuerungsgruppe.html) ([Matthias Boenig](https://tboenig.github.io/), [Daniel Burckhardt](https://www.ghi-dc.org/ghi-staff/research-service/daniel-burckhardt.html), [Stefan Dumont](http://www.bbaw.de/die-akademie/mitarbeiter/dumont), [Alexander Geyken](http://www.bbaw.de/die-akademie/mitarbeiter/geyken), [Martina
  Gödel](http://textloop.de/werdegang/), [Susanne Haaf](https://www.uni-leipzig.de/personenprofil/mitarbeiter/susanne-haaf-dumont), [Axel Herold](http://www.bbaw.de/die-akademie/mitarbeiter/herold), [Christian Thomas)](http://www.bbaw.de/die-akademie/mitarbeiter/thomas)
* Schema, Dokumentation & Pflege des Formats bis 2023: Susanne Haaf
* Entwicklung des Formats (bis 2017): Matthias Boenig, Alexander Geyken, Susanne Haaf, Christian Thomas, Frank Wiegand
* Vorarbeiten (bis 2010): Oliver Duntze, Christiane Fritze, Alexander Geyken

Kontakt: [redaktion@deutschestextarchiv.de](mailto:redaktion@deutschestextarchiv.de)

Das Tagset des DTA-Basisformats basiert auf den [P5-Richtlinien der Text Encoding Initiative (TEI)](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/index.html).

## Technische Realisierung der Dokumentationsseiten

Diese Dokumentation basiert auf dem XML-Dokumentationsformat
[DITA (Darwin Information Typing Architecture)](http://docs.oasis-open.org/dita/v1.2/spec/DITA1.2-spec.html).

Die mobile Webseite wurde mithilfe des
[oXygen XML Editors](https://www.oxygenxml.com/) erstellt und
an das Design des Deutschen Textarchivs angepasst.

Technische Realisierung und Anpassungen: Susanne Haaf, unter Mitarbeit von Matthias Boenig


---

## Das DTA-Basisformat

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/index.html](https://www.deutschestextarchiv.de/doku/basisformat/index.html)

[Einführung](einfuehrung.html)

Zielsetzung des DTA-Basisformats, zugehörige Publikationen, Nutzung und erste Schritte

[Metadaten](metadaten.html)

Erfassung (Transkription) und Auszeichnung von Metadaten

[Transkription](transkription.html)

Richtlinien zur Erfassung der Volltexte

[Formal](texterschliessung_formal.html)

Auszeichnung von formalen Strukturen in Volltexten (Besonderheiten in Typographie und Layout)

[Inhaltlich](texterschliessung_inhaltlich.html)

Auszeichnung von inhaltsbezogenen (logischen, konzeptuellen) Strukturen in Volltexten

[Spezial](besondereTextsorten.html)

Auszeichnung spezifischer Textarten und Textsorten (Manuskripte; Zeitungen)

[Übersichten](uebersichten.html)

Das Tagset im Überblick

[Impressum](impressum.html)

Impressum, Nutzungsbedingungen, Kontaktdaten sowie Hinweise zum Datenschutz


---

## Inhaltsverzeichnis

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/inhaltsverzeichnis.html](https://www.deutschestextarchiv.de/doku/basisformat/inhaltsverzeichnis.html)

# Inhaltsverzeichnis

Inhaltsverzeichnisse werden mit dem Element `<div
type="contents">` umschlossen. Ein möglicher Titel steht in
dem Unterelement `<head>`. Die einzelnen
Verzeichniseinträge werden in einer Liste (`<list>`)
organisiert, wobei die jeweiligen Kapitelhinweise in
`<item>`-Elementen, die jeweils zugehörigen
Seitenzahlen in `<ref>`-Elementen stehen. Das jeweilige
`<ref>`-Element kann mit einem `@target`-Attribut
versehen werden, das über die Faksimile-Nummer auf die referenzierte Seite verweist (Level 3).

```
<div type="contents">
  <head>[Titel]</head><!-- falls vorhanden -->
  <list>
    <item>[Verzeichniseintrag1/Kapitelname1]
      <ref>[Seite]</ref>
    </item>
    <item>[Verzeichniseintrag2/Kapitelname2]
      <ref>[Seite]</ref>
    </item>
  </list>
</div>
```

Inhaltsverzeichnisse können im einleitenden Teil eines Bandes und somit
innerhalb des `<front>`-Elements stehen oder einen
Band beschließen, in welchem Fall sie dem
`<back>`-Element zuzuordnen sind.
Inhaltsverzeichnisse zu einzelnen Büchern eines Bandes werden schließlich
innerhalb des `<text>`-Elements transkribiert.

HINWEIS:

***Abweichende Regelung Phase 1:** Typographische Besonderheiten (fett, kursiv,
gesperrt etc.) des Inhaltsverzeichnisses gegenüber dem Fließtext sowie
typographische Varianz innerhalb des Inhaltsverzeichnisses werden mit
ausgezeichnet.*

## Kodierung von Inhaltsverzeichnissen

![](img/KWBp0ll1jb.png)

```
<div type="content">
  <head>
    <hi rendition="#c #b">Inhalt.</hi><lb/>
  </head>
  <list>
    <item><hi rendition="#right">Seite</hi></item><lb/>
    <item>
      I. Die Geschichte der Zellengranula<space dim="horizontal"/><ref>1</ref>
    </item><lb/>
    <item>
      II. Die Methoden der Granulauntersuchung<space dim="horizontal"/><ref>17</ref>
    </item><lb/>
    <item>
      III. Körner und Fäden der Zellen<space dim="horizontal"/><ref>39</ref>
    </item><lb/>
    <item>
      IV. Die Leber von Rana esculenta<space dim="horizontal"/><ref>56</ref>
    </item><lb/>
    <item>
      V. Die Fettumsetzungen in den Zellen<space dim="horizontal"/><ref>76</ref>
    </item><lb/>
    <item>
      VI. Die Secretionserscheinungen in den Zellen <space dim="horizontal"/><ref>97</ref>
    </item><lb/>
    <item>
      VII. Die Genese der Zelle<space dim="horizontal"/><ref>123</ref>
    </item><lb/>
    <item>
      Erklärungen zu den Tafeln<space dim="horizontal"/><ref>143</ref>
    </item>
  </list>
</div><lb/>
```

*Quelle: [Altmann, Richard: Die
Elementarorganismen und ihre Beziehungen zu den Zellen. Leipzig,
1890. [Faksimile 15]](http://www.deutschestextarchiv.de/altmann_elementarorganismen_1890/15)*


---

## Initialen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/initiale.html](https://www.deutschestextarchiv.de/doku/basisformat/initiale.html)

# Initialen

## Kodierung von Initialen (1)

![](img/zOxTW_9m2f.png)

```
<hi rendition="#in">V</hi>a&#x0364;terchen
```

*Quelle: [Campe, Joachim Heinrich: Robinson der Jüngere. Bd. 2.
Hamburg, 1780. [Faksimile 9]](http://www.deutschestextarchiv.de/campe_robinson02_1780/9)*

## Kodierung von Initialen (2)

![](img/tn154ms3HG.png)

```
<hi rendition="#in">D</hi>u
```

*Quelle: [Goeze, Johann August Ephraim: Zeitvertreib und
Unterricht für Kinder vom dritten bis zehnten Jahr in kleinen Geschichten. Bd. 1.
Leipzig, 1783. [Faksimile 38]](http://www.deutschestextarchiv.de/goetze_zeitvertreib01_1783/38)*

## Kodierung von Initialen (3)

![](img/gA_M6EFBDV.png)

```
<hi rendition="#in">A</hi>poll! nimm deine Leyer wieder,
```

*Quelle: [Karsch, Anna Luise: Gedichte. Berlin, 1792. [Faksimile
188]](http://www.deutschestextarchiv.de/karsch_gedichte_1792/188)*

Initialen werden immer nur einmal wiedergegeben, auch wenn sie sich über mehrere Zeilen
erstrecken. Die Größe der jeweiligen Initiale wird nicht gesondert vermerkt.

## Umgang mit mehrzeiligen Initialen

![](img/NrdJwXFcOf.png)

```
<hi rendition="#in">J</hi>ch
```

*Quelle: [Goeze, Johann August Ephraim: Zeitvertreib und
Unterricht für Kinder vom dritten bis zehnten Jahr in kleinen Geschichten. Bd. 1.
Leipzig, 1783. [Faksimile 9]](http://www.deutschestextarchiv.de/goetze_zeitvertreib01_1783/9)*


---

## Inhaltliche Inline-Auszeichnungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/inlineAnnotation.html](https://www.deutschestextarchiv.de/doku/basisformat/inlineAnnotation.html)

# Inhaltliche Inline-Auszeichnungen

## Themen

* [Fremdsprachliches Material](fremdsprachlMaterial.html)
* [Eigennamen](eigenname.html)
* [Datumsangaben](datum.html)


---

## Introduction to the DTABf

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/introduction_en.html](https://www.deutschestextarchiv.de/doku/basisformat/introduction_en.html)

# Introduction to the DTABf

## Introduction

The structural annotation of all DTA texts is done according to the DTA ›Base Format‹ (DTABf).
The DTABf was developed in accordance with the P5-Guidelines of the
[Text Encoding Initiative (TEI)](http://www.tei-c.org/). Since the TEI Guidelines
are offering solutions for a huge amount of tagging requirements and are thus rather extensive
and flexible, they are meant to be adjusted to the individual necessities of projects working
with the TEI. For the DTA this was achieved by creation of the DTABf, a proper subset of the
TEI/P5 tagset, which offers not only fixed sets of elements but also of corresponding attributes
and (where applicable) values. The DTABf tagset is fully conformant with the TEI/P5-Guidelines,
i.e. the TEI tagset was only reduced not extended in any way.

The DTABf is part of the DTA Guidelines, which also contain General Guidelines
and the Transcription Guidelines. It is supposed to
allow for unrestricted tagging regarding possible structural phenomena while at the
same time avoiding ambiguities regarding the tagging of similar phenomena. This way
we want to ensure coherence in text structuring within the whole DTA corpus. Regarding
the wide temporal coverage of the DTA corpus as well as the diversity of text types and
genres this named intend of the DTABf turns out to be a huge challenge due to the fact
that the heterogeneity of texts is accompanied by a huge structural variability among
the original text sources.

With the DTABf we are proposing a standardized format for the structural annotation
of digitized historical texts. The advantage of such an approach is that diverse
TEI texts become analyzable not only by similar methods but also in comparison with
one another. The underlying annotation guidelines of the DTABf are documented extensively,
this way ensuring that the tagging remains comprehensive. Thus, DTABf conformity not
only facilitaes the integration of TEI texts into the DTA infrastructure but also
their re-use inside other full text archives.

## DTABf Documentation (German)

* [Introduction to the DTABf ⇗](ziel.html)
* [Structuring of Metadata ⇗](metadaten.html "Erfassung (Transkription) und Auszeichnung von Metadaten")
* [Transcription Guidelines ⇗](transkription.html "Richtlinien zur Erfassung der Volltexte")
* [Structuring of Formal (Typographic) Phenomena ⇗](texterschliessung_formal.html "Auszeichnung von formalen Strukturen in Volltexten (Besonderheiten in Typographie und Layout)")
* [Structuring of Semantic (Meaningful) Phenomena ⇗](texterschliessung_inhaltlich.html "Auszeichnung von inhaltsbezogenen (logischen, konzeptuellen) Strukturen in Volltexten")
* Besondere Textsorten
  + [Structuring of Manuscripts ⇗](manuskript.html)
  + [Structuring of Newspapers and Journals ⇗](zeitung.html)
* Übersichten
  + [Overview of all DTABf-Elements within the `<teiHeader>` area ⇗](uebersichtHeader.html)
  + [Overview of all DTABf-Elements within the `<text>`area ⇗](uebersichtText.html)
* [Boilerplate DTABf document ⇗](http://www.deutschestextarchiv.de/files/vorlage_basisformat.xml)

## DTABf Schema

* [DTABf for prints: RNG schema⇗](http://www.deutschestextarchiv.de/basisformat.rng)
* [DTABf for prints: ODD ⇗](http://www.deutschestextarchiv.de/basisformat.odd)
* [DTABf for manuscripts: RNG schema⇗](http://www.deutschestextarchiv.de/basisformat_ms.rng)
* [DTABf for manuscripts: ODD ⇗](http://www.deutschestextarchiv.de/basisformat_ms.odd)
* [DTABf Schematron constraints set ⇗](http://www.deutschestextarchiv.de/basisformat.sch)

## Useful Tools and Applications

**Webform for Metadata Entry:**

The DTA provides a web form, which facilitates the creation of DTABf conformant TEI Headers.
This way, users do not have to write the quite complex TEI-Headers by themselves but can
fill out the form and automatically generate a DTABf conformant TEI Header.

* [Webform for Metadata Entry](http://www.deutschestextarchiv.de/dtae/submit/clarin)

**Framework for Text Entry:**

For text transcription and DTABf conformant annotation, the DTA offers a framework for the author
mode of the oXygen XML-Editor. This DTA-oXygen-Framework DTAoX enables users to obtain an immediate
visualization of their annotated texts as well as to transcribe and annotate texts from scratch in
a WYSIWYG-like environment. DTAoX is available under the GNU Lesser General Public License (LGPL).
The current version has been optimized for the oXygen versions 14.2 and 15.

* Version 1.1.1 (November 29th, 2013): [Framework](http://www.deutschestextarchiv.de/files/DTAoX-1.1.1.zip) (.zip)


---

## Grundregeln zur Auszeichnung von Zeitungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/jAllg.html)

# Grundregeln zur Auszeichnung von Zeitungen

Die Auszeichnung von Zeitungen und Periodika erfolgt grundsätzlich entsprechend dem DTA-Basisformat.
Die vorliegende Spezifikation bezieht sich lediglich auf Besonderheiten von Zeitungstexten,
die im DTA-Basisformat nicht berücksichtigt sind.

Grundsätzlich werden Zeitungs- und Zeitschriftenausgaben als in sich geschlossene Dokumente betrachtet und in
Gänze erfasst. Dieses Verfahren sollte angestrebt werden. In Ausnahmefällen ist es darüber
hinaus möglich, einzelne Artikel einer Ausgabe als separate Dokumente aufzunehmen.
Führt dies zu textuellen Auslassungen auf einer Seite, so werden diese mittels
`<gap reason="insignificant"/>` ausgezeichnet
(vgl. [Kapitel: Schwer bzw. nicht entzifferbare Zeichen und Auslassungen](gapSupplied.html)).


---

## Anzeigen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jAnnouncements.html](https://www.deutschestextarchiv.de/doku/basisformat/jAnnouncements.html)

# Anzeigen

Für Anzeigenteile einer Zeitungs-/Zeitschriftenausgabe steht der Wert `jAnnouncements` im `@type`-Attribut
eines `<div>`-Elements erster Ebene. Die einzelne Anzeige wird jeweils wiederum durch
ein `<div>`-Element tieferer Ebene umschlossen, welches das Attribut-Wert-Paar
`@type="jAn"` (für "announcement") erhält.

| Kategorie | `@type`-Wert | Hierarchie-Ebene (empfohlen) |
| --- | --- | --- |
| Anzeigenteil | `jAnnouncements` | 1 |
| Anzeige | `jAn` | 2 | 3 | ... |

```
<div type="jAnnouncements">
  <div type="jAn">[Anzeige]</div>
  <div type="jAn">[Weitere Anzeige]</div>
</div>
```

Sind innerhalb des Anzeigenteils einzelne Anzeigen wiederum gruppiert, so
können mehrere `<div type="jAnnouncements">`-Elemente ineinander
geschachtelt werden.

```
<div type="jAnnouncements">
  <div type="jAnnouncements"> <!-- erste Gruppe von Anzeigen -->
    <div type="jAn">[Anzeige]</div>
    <div type="jAn">[Weitere Anzeige]</div>
  </div>
  <div type="jAnnouncements"> <!-- zweite Gruppe von Anzeigen -->
    <div type="jAn">[Anzeige]</div>
    <div type="jAn">[Weitere Anzeige]</div>
  </div>
</div>
```

Achtung:

Der DTABf-konforme `@type`-Wert
`"advertisement"` für `<div>`-Elemente
ist in Zeitungen/Zeitschriften nicht zulässig. Statt dessen ist
`"jAn"` zu verwenden.


---

## Sonstige Artikel

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jArtOther.html](https://www.deutschestextarchiv.de/doku/basisformat/jArtOther.html)

# Sonstige Artikel

Kann eine Gruppe von Beiträgen nicht einer der genannten Kategorien zugeordnet werden, so
werden diese Beiträge in untypisierten `<div>`-Elementen zusammengefasst.

```
<div n="[Ebene]"><!-- nicht-spezifizierbarer Beitrag -->
  <p>[Beitragstext]</p>
</div>

```


---

## Strukturierung innerhalb eines Artikels

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jArtStruct.html](https://www.deutschestextarchiv.de/doku/basisformat/jArtStruct.html)

# Strukturierung innerhalb eines Artikels

**Titel von Artikeln oder Artikelgruppen** werden jeweils im `<head>`-Element
des `<div>`-Elements wiedergegeben.
(Vgl. [Kapitel: Texteinteilung auf Kapitelebene](div.html).)

**Angaben zum Autor, Ort und Datum zu Beginn eines Artikels** werden als Titel des Artikels behandelt und im
Element `<head>` wiedergegeben. Die Autorangabe bzw. dessen Korrespondenzzeichen
steht im Element `<bibl>`, welches das Unterelement `<author>`
erhält. Die Orts- und Datumsangabe erfolgt im Element `<dateline>`.

```
<div type="jArticle">
  <head>
    <bibl>
      <author>[Autorname oder Korrespondenzzeichen]</author>
    </bibl>
    <dateline>[Ort, Datum]</dateline>
  </head>
</div>
```

Stehen die **Angaben zum Autor, Ort und Datum am Artikelende**, so werden sie am Ort
ihres Auftretens mittels <bibl>/<author> bzw. <dateline> wiedergegeben.

```
<div type="jArticle">
  <p>[Artikeltext]</p>
  <bibl>
    <author>[Autorname oder Korrespondenzzeichen]</author>
  </bibl>
  <dateline>[Ort, Datum]</dateline>
</div>
```

Die **Texterfassung** erfolgt seitenweise, wobei der Text einer Seite von der linken oberen Ecke aus
artikelweise erfasst wird. Jeder Artikel erhält ein Attribut `@xml:id`, über welches jeweils
eine eindeutige ID zugeordnet wird.


---

## Berichte, Nachrichten, Kommentare

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jArticle.html](https://www.deutschestextarchiv.de/doku/basisformat/jArticle.html)

# Berichte, Nachrichten, Kommentare

Berichte und Nachrichten verschiedener Art, die in der Quelle unter einem thematischen Aspekt
gruppiert wurden (i.d.R. Politische Nachrichten, Wirtschaftsnachrichten, Wetterberichte),
werden in entsprechend typisierten `<div>`-Elementen der obersten Ebene
zusammengefasst.

Die einzelnen Artikel innerhalb dieser Rubriken werden jeweils wiederum durch
`<div>`-Elemente tieferer Ebene umschlossen, welche das Attribut-Wert-Paar
`@type="jArticle"` erhalten.

| Kategorie | `@type`-Wert | Hierarchie-Ebene (empfohlen) |
| --- | --- | --- |
| Kulturnachrichten | `jCulturalNews` | 1 |
| Lokales | `jLocal` | 1 |
| Politische Nachrichten inkl. telegraphischer Berichte | `jPoliticalNews` | 1 |
| Vermischtes | `jVarious` | 1 |
| Wetternachrichten | `jWeatherReports` | 1 |
| Wirtschafts- und Finanznachrichten | `jFinancialNews` | 1 |
| Artikel/Nachricht | `jArticle` | 2 | 3 | ... |
| Kommentar | `jComment` | 1 | 2 | ... |

```
<body>
  <div type="jPoliticalNews">
    <div type="jArticle">[Politische Nachricht]</div>
    <div type="jArticle">[Weitere politische Nachricht]</div>
  </div>
  <div type="jFinancialNews">
    <div type="jArticle">[Wirtschaftsnachricht]</div>
    <div type="jArticle">[Weitere Wirtschaftsnachricht]</div>
  </div>
  <div type="jWeatherReports">
    <div type="jArticle">[Wetternachricht]</div>
    <div type="jArticle">[Weitere Wetternachricht]</div>
  </div>
</body>
```

Sind die Artikel innerhalb einer Rubrik wiederum gruppiert (z.B. Gruppierung der Artikel nach
Nationalstaaten innerhalb der Politischen Nachrichten, i.e. "Deutschland", "Frankreich", etc.),
so können die Rubriken (`"jPoliticalNews"`, `"jFinancialNews"`, etc.)
in sich geschachtelt werden.

```
<div type="jPoliticalNews"> <!-- Rubrik politische Nachrichten -->
  <div type="jPoliticalNews"> <!-- Spezialgruppe politischer Nachrichten, z.B. "Deutschland" -->
    <head>[Subtitel, z.B. "Deutschland"]</head>
    <div type="jArticle">[Politische Nachricht aus Deutschland]</div>
    <div type="jArticle">[Weitere politische Nachricht aus Deutschland]</div>
  </div>
  <div type="jPoliticalNews"> <!-- Spezialgruppe politischer Nachrichten, z.B. "Frankreich" -->
    <head>[Subtitel, z.B. "Frankreich"]</head>
    <div type="jArticle">[Politische Nachricht aus Frankreich]</div>
    <div type="jArticle">[Weitere politische Nachricht aus Frankreich]</div>
  </div>
</div>
```


---

## Arten von Artikeln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jArticleTypes.html](https://www.deutschestextarchiv.de/doku/basisformat/jArticleTypes.html)

# Arten von Artikeln

## Themen

* [Berichte, Nachrichten, Kommentare](jArticle.html)
* [Feuilleton](jFeuilleton.html)
* [Anzeigen](jAnnouncements.html)
* [Leserbriefe](jLetters.html)
* [Sonstige Artikel](jArtOther.html)


---

## Abschließende Textstücke

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jBack.html](https://www.deutschestextarchiv.de/doku/basisformat/jBack.html)

# Abschließende Textstücke

Abschließende Teile, z.B. das Impressum, am Schluss der Ausgabe werden im Element `<back>`
wiedergegeben. Darin steht ein Nachsatz im Element `<trailer>`, ein mögliches Impressum
im Element `<div type="imprint">` (s. Kap. [Einleitende Textstücke](jFront.html); vgl. außerdem
[Kapitel: Anhang](anhang.html)).


---

## Beilagen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jBeilagen.html](https://www.deutschestextarchiv.de/doku/basisformat/jBeilagen.html)

# Beilagen

Beilagen zu Zeitungen werden im Element `<floatingText>` wiedergegeben, welches im Anschluss
an die übergeordnete Zeitungsausgabe im `<body>`-Bereich (in Ausnahmefällen im
`<back>`-Bereich) steht. Das Element `<floatingText>` steht
dabei immer innerhalb eines übergeordneten `<div>`-Elements der ersten Ebene.

Innerhalb des `<floatingText>`-Elements können erneut die grundlegenden
Strukturelemente von TEI-Dokumenten `<front>`, `<body>`
und `<back>` stehen. Für die Strukturierung der Beilage steht das Inventar
der Strukturierung von Zeitungsausgaben und Periodika im Allgemeinen zur Verfügung.

```
<body> <!-- Text der Hauptausgabe -->
  <div type="jPoliticalNews"> <!-- Politische Nachrichten der Hauptausgabe -->
    <div type="jArticle">[Politische Nachricht]</div>
    <div type="jArticle">[Weitere politische Nachricht]</div>
  </div>
  <div type="jFinancialNews"> <!-- Wirtschaftsnachrichten der Hauptausgabe -->
    <div type="jArticle">[Wirtschaftsnachricht]</div>
    <div type="jArticle">[Weitere Wirtschaftsnachricht]</div>
  </div>
  <div type="jSupplement"> <!-- Beilage -->
    <floatingText>
      <front>[Titelzeile der Beilage]</front>
      <body> <!-- Text der Beilage -->
        <div type="jPoliticalNews"> <!-- Politische Nachrichten der Beilage -->
          <div type="jArticle">[Politische Nachricht]</div>
          <div type="jArticle">[Weitere politische Nachricht]</div>
        </div>
        <div type="jFinancialNews"> <!-- Wirtschaftsnachrichten der Beilage -->
          <div type="jArticle">[Wirtschaftsnachricht]</div>
          <div type="jArticle">[Weitere Wirtschaftsnachricht]</div>
        </div>
      </body>
      <back>[Abschließende Textstücke der Beilage]</back>
    </floatingText>
  </div>
</body>
```


---

## Erfassung und Strukturierung des Textkörpers

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jBody.html](https://www.deutschestextarchiv.de/doku/basisformat/jBody.html)

# Erfassung und Strukturierung des Textkörpers

## Themen

* [Textkörper Zeitungen allgemein](jBodyAllg.html)
* [Artikeltypen](jArticleTypes.html)
* [Artikelstruktur](jArtStruct.html)
* [Verknüpfungen](jLinking.html)


---

## Allgemeine Hinweise zur Erfassung und Strukturierung des Textkörpers bei Zeitungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jBodyAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/jBodyAllg.html)

# Allgemeine Hinweise zur Erfassung und Strukturierung des Textkörpers bei Zeitungen

Die **Grundstrukturierung** innerhalb der Zeitung/Zeitschrift erfolgt mittels
`<div>`-Elementen. Dabei werden Gruppen von Artikeln ebenso wie die
einzelnen Artikel selbst von typisierten `<div>`-Elementen umschlossen.
Die möglichen Werte für die jeweiligen `<div>`-Elemente werden im
Folgenden näher vorgestellt.


---

## Feuilleton

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jFeuilleton.html](https://www.deutschestextarchiv.de/doku/basisformat/jFeuilleton.html)

# Feuilleton

Beiträge des Feuilletons werden im Element `<div type="jFeuilleton">`
zusammengefasst. Die einzelnen Feuilletonartikel werden jeweils durch `<div>`-Elemente
tieferer Ebene umschlossen, welche das Attribut-Wert-Paar @type="jArticle" erhalten.

| Kategorie | `@type`-Wert | Hierarchie-Ebene (empfohlen) |
| --- | --- | --- |
| Feuilleton | `jFeuilleton` | 1 |
| Feuilletonartikel | `jArticle` | 2 | 3 | ... |

```
<div type="jFeuilleton">
  <div type="jArticle">[Feuilletonartikel]</div>
  <div type="jArticle">[Weiterer Feuilletonartikel]</div>
</div>
```

Sind innerhalb des Feuilletons einzelne Artikel wiederum gruppiert, so
können mehrere `<div type="jFeuilleton">`-Elemente
ineinander geschachtelt werden.

```
<div type="jFeuilleton"> <!-- Rubrik Feuilleton -->
  <div type="jFeuilleton"> <!-- erste Gruppe von Feuilleton-Artikeln -->
    <div type="jArticle">[Feuilletonartikel]</div>
    <div type="jArticle">[Weiterer Feuilletonartikel]</div>
  </div>
  <div type="jFeuilleton"> <!-- zweite Gruppe von Feuilleton-Artikeln -->
    <div type="jArticle">[Feuilletonartikel]</div>
    <div type="jArticle">[Weiterer Feuilletonartikel]</div>
  </div>
</div>
```


---

## Einleitende Textstücke

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jFront.html](https://www.deutschestextarchiv.de/doku/basisformat/jFront.html)

# Einleitende Textstücke

## Themen

* [Titelkopf](jHeading.html)
* [Einführende Informationen](jIntroMaterial.html)


---

## Der Titelkopf

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jHeading.html](https://www.deutschestextarchiv.de/doku/basisformat/jHeading.html)

# Der Titelkopf

Der Titelkopf der jeweiligen Ausgabe steht im `<front>`-Bereich des
TEI-Dokuments. Er wird mit dem Element `<titlePage>` umschlossen, welches das
Attribut-Wert-Paar @type="heading" erhält, um anzuzeigen, dass der Titel- bzw. Zeitungskopf
nicht wie gewöhnlich eine gesamte Titelseite umfasst.

Der Titel der Zeitungs- bzw. Zeitschriftenausgabe wird innerhalb `von <titlePage>` mit dem Element
`<docTitle>` umschlossen. Die einzelnen Teile des Titels stehen innerhalb
von `<docTitle>` in einzelnen `<titlePart>`-Elementen.
Dabei erhält `<titlePart>` das Attribut @type mit den
möglichen Werten "main" (Haupttitel) und "sub" (Untertitel).

Eine Druckerlaubnis zu Beginn der Titelei wird innerhalb des `<docTitle>`-Elements im Element
`<titlePart>` wiedergegeben, welches das für Zeitungen/Zeitschriften spezifische Attribut-Wert-Paar
@type="jImprimatur" erhält. Steht die Druckerlaubnis am Schluss der Titelei oder am Schluss
der Ausgabe, so wird sie mit dem Element `<div type="imprimatur">` umschlossen.

Hinweise zum Druck werden im Element `<docImprint>` wiedergegeben.
Dabei steht das Datum der Ausgabe im Unterelement `<docDate>`, der
Publikationsort im Unterelement `<pubPlace>` und die mögliche
Angabe der Druckerei (Impressum) im Unterelement `<publisher>`. (Vgl.
[Kapitel: Titelblatt](titelblatt.html).)

Achtung:

Steht das Impressum nicht am Beginn, sondern am Schluss der Ausgabe, so
wird dieses an der Stelle seines Vorkommens mit dem Element `<div type="imprint">`
kodiert. (Vgl. [Kapitel: Anhang](anhAllg.html).)

```
<front>
  <titlePage type="heading">
    <docTitle>
      <titlePart type="jImprimatur">[Druckerlaubnis]</titlePart> <!-- gegebenenfalls -->
      <titlePart type="main">[Haupttitel der Ausgabe]</titlePart>
      <titlePart type="sub">[Untertitel der Ausgabe]</titlePart>
    </docTitle>
    <docImprint>
      <docDate>[Datum der Ausgabe]</docDate>
      <pubPlace>[Erscheinungsort]</pubPlace>
      <publisher>[Druckerei-/Verlagsangabe]</publisher>
    </docImprint>
  </titlePage>
</front>

```


---

## Einführende Informationen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jIntroMaterial.html](https://www.deutschestextarchiv.de/doku/basisformat/jIntroMaterial.html)

# Einführende Informationen

Einführende Informationen zur jeweiligen Zeitungs-/Zeitschriftenausgabe, die außerhalb des Titelkopfs
erscheinen, werden ebenfalls im `<front>`-Element in entsprechend
typisierten `<div>`-Elementen wiedergeben. Folgende Werte kann
@type in `<div>` dabei annehmen:

| `@type`-Wert | Bedeutung |
| --- | --- |
| contents | Inhaltsverzeichnis |
| jExpedition | Angaben zu Versand und Preis (Expedition) |
| jEditorialStaff | Zusammenstellung der Redaktion |
| imprimatur | Druckerlaubnis |

```
<front>
  <titlePage>[Titelei]</titlePage>
  <div type="contents">[Inhaltsverzeichnis]</div>
  <div type="jEditorialStaff">[Zusammenstellung der Redaktion]</div>
  <div type="jExpedition">[Hinweise zu Versand und Preis]</div>
  <div type="imprimatur">[Druckerlaubnis]</div>
</front>

```


---

## Leserbriefe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jLetters.html](https://www.deutschestextarchiv.de/doku/basisformat/jLetters.html)

# Leserbriefe

Leserbriefe werden durch `<div>`-Elemente erster Ebene umschlossen, welche das
Attribut-Wert-Paar `@type="jReadersLetters"` erhalten. Der jeweilige Brief wird durch ein
`<div>`-Element tieferer Ebene umschlossen, welches den `@type`-Wert
`"letter"` erhält.

| Kategorie | `@type`-Wert | Hierarchie-Ebene (empfohlen) |
| --- | --- | --- |
| Leserbriefe | `jReadersLetters` | 1 |
| Brief | `letter` | 2 | 3 | ... |

```
<div type="jReadersLetters">
  <div type="letter">[Brief]</div>
  <div type="letter">[Weiterer Brief]</div>
</div>
```

Sind innerhalb der Rubrik "Leserbriefe" einzelne Leserbriefe wiederum gruppiert, so
können mehrere `<div type="jReadersLetters">`-Elemente
ineinander geschachtelt werden.

```
<div type="jReadersLetters"> <!-- Rubrik Leserbriefe -->
  <div type="jReadersLetters"> <!-- erste Gruppe von Leserbriefen -->
    <div type="letter">[Leserbriefl]</div>
    <div type="letter">[Weiterer Leserbrief]</div>
  </div>
  <div type="jReadersLetters"> <!-- zweite Gruppe von Leserbriefen -->
    <div type="letter">[Leserbrief]</div>
    <div type="letter">[Weiterer Leserbrief]</div>
  </div>
</div>
```


---

## Verknüpfungen diskontinuierlicher Artikelteile

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/jLinking.html](https://www.deutschestextarchiv.de/doku/basisformat/jLinking.html)

# Verknüpfungen diskontinuierlicher Artikelteile

Wird ein Artikel unterbrochen, entweder, weil er in einer späteren Ausgabe fortgesetzt wird, oder,
weil innerhalb der Ausgabe Beiträge einer anderen Kategorie (z.B. des Feuilletons) eingeschoben
werden, so werden die Teile des betreffenden Artikels miteinander verknüpft.

Innerhalb einer Ausgabe erfolgt die Verknüpfung durch die Attribute `@prev`, `@next`
und `@xml:id`. Für eine genauere Beschreibung dieser Verknüpfungsmethode vgl.
[Kapitel: Einschübe und diskontinuierliche Textpassagen](einschub.html).

Wird ein Artikel unterbrochen und in einer späteren Ausgabe fortgesetzt, so erfolgt die Verknüpfung
der einzelnen Teilartikel über das `<ref>`-Element, welches entweder leer ist oder
den in der Quelle gegebenen Hinweis auf eine folgende Forsetzung umschließt. Sämtliche Teile eines
Artikels werden mit `<ref>`-Elementen versehen. Diese stehen am Schluss des
Teilartikels, falls in einer späteren Ausgabe eine Fortsetzung folgt, oder am Beginn eines Artikels,
falls auf einen vorhergehenden Teilartikel verwiesen werden soll. Der eigentliche Verweis erfolgt
über das Attribut `@target`, welches den Pfad zu dem entsprechenden Artikel sowie die
eindeutige Artikel-ID enthält.

**Beispiel: Verknüpfung von drei Artikelteilen in unterschiedlichen Ausgaben**

```
<body><!-- Ausgabe 1 -->
  <!-- [...] -->
  <div type="jArticle" xml:id="[xml:id-Teil-1]"><!-- Artikel Teil 1 -->
    <p>[Beginn des Artikels]</p>
    <p>[weiterer Artikeltext]</p>
    <p>
      <ref target="[URI-Ausgabe-2/xml:id-Teil-2]">[Hinweis auf Fortsetzung, z.B. "Forts. folgt"]</ref>
    </p>
  </div>
  <!-- [...] -->
</body>
<body><!-- Ausgabe 2 -->
  <!-- [...] -->
  <div type="jArticle" xml:id="[xml:id-Teil-2]"><!-- Artikel Teil 2 -->
    <p><ref target="[URI-Ausgabe-1/xml:id-Teil-1]"/></p>
    <p>[Artikeltext]</p>
    <p>[weiterer Artikeltext]</p>
    <p>
      <ref target="[URI-Ausgabe-3/xml:id-Teil-3]">[Hinweis auf Fortsetzung, z.B. "Forts. folgt"]</ref>
    </p>
  </div>
  <!-- [...] -->
</body>
<body><!-- Ausgabe 3 -->
  <!-- [...] -->
  <div type="jArticle" xml:id="[xml:id-Teil-3]"><!-- Artikel Teil 3 -->
    <p>
      <ref target="[URI-Ausgabe-2/xml:id-Teil-2]"/>
    </p>
    <p>[Artikeltext]</p>
    <p>[Schluss des Artikels]</p>
  </div>
  <!-- [...] -->
</body>

```


---

## Kapitälchen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/kapitaelchen.html](https://www.deutschestextarchiv.de/doku/basisformat/kapitaelchen.html)

# Kapitälchen

## Kodierung von Kapitälchen

![](img/E8wtUz6x2i.png)

```
<hi rendition="#k">Ando-Tsus-sima-no-Kami</hi>
```

*Quelle: [[Berg, Albert]: Die preussische Expedition nach
Ost-Asien. Bd. 1. Berlin, 1864. [Faksimile 380]](http://www.deutschestextarchiv.de/berg_ostasien01_1864/380)*


---

## Horizontale Klammerungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klHorizontal.html](https://www.deutschestextarchiv.de/doku/basisformat/klHorizontal.html)

# Horizontale Klammerungen

Einen Spezialfall bilden Stammbäume, die in der Regel mittels
horizontalen Klammerungen visualisiert werden. Sie
werden als Tabellen wiedergegeben
(`<table>`,
`<row>`,
`<cell>`). Dabei erhält das
`<cell>`-Element ein
`@rendition`-Attribut mit den
möglichen Werten `"#topBraced"` (für
Klammerungen oberhalb der betreffenden Zelle) und
`"#bottomBraced"` (für
Klammerungen unterhalb der betreffenden Zelle).

## Umgang mit horizontalen Klammerungen

![](img/EHfye1h9gi.png)

```
<note place="foot" n="*">Der Stammbaum der numidischen Fürsten ist folgender:<lb/>
  <table>
    <row>
      <cell cols="6" rendition="#bottomBraced"><hi rendition="#g">Massinissa</hi> 516-605.</cell>
    </row>
    <row>
      <cell cols="3" rendition="#bottomBraced"><hi rendition="#g">Micipsa</hi><lb/>† 636</cell>
      <cell rendition="#bottomBraced"><hi rendition="#g">Gulussa</hi><lb/>† vor 636</cell>
      <cell cols="2" rendition="#bottomBraced"><hi rendition="#g">Mastanabal</hi><lb/>† vor 636</cell>
    </row>
    <row>
      <cell rows="4"><hi rendition="#g">Adherbal</hi><lb/>† 642</cell>
      <cell rows="4"><hi rendition="#g">Hiempsal</hi> I<lb/>† c. 637</cell>
      <cell rows="4">Micipsa<lb/>(Diod. p. † 607)</cell>
      <cell rows="4">Massiva<lb/>† 643</cell>
      <cell rendition="#bottomBraced"><hi rendition="#g">Gauda</hi><lb/>† vor 672</cell>
      <cell><hi rendition="#g">Jugurtha</hi><lb/>† 650</cell>
    </row>
    <row>
      <cell rendition="#bottomBraced"><hi rendition="#g">Hiempsal</hi> II</cell>
      <cell rows="3">Oxyntas</cell>
    </row>
    <row>
      <cell rendition="#bottomBraced"><hi rendition="#g">Juba</hi> I</cell>
    </row>
    <row>
      <cell><hi rendition="#g">Juba</hi> II</cell>
    </row>
  </table>
</note>
```

*Quelle: [Mommsen,
Theodor: Römische Geschichte. Bd. 2: Von
der Schlacht bei Pydna bis auf Sullas
Tod. Leipzig, 1855. [Faksimile
142]](http://www.deutschestextarchiv.de/mommsen_roemische02_1855/142)*


---

## Klammerungen in Listen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klListe.html](https://www.deutschestextarchiv.de/doku/basisformat/klListe.html)

# Klammerungen in Listen

Klammerungen von Textstücken treten häufig innerhalb von Listen oder Listenähnlichen
Strukturen auf. Sie werden innerhalb der übergeordneten Liste durch ein eigenes
`<item>`-Element umschlossen, innerhalb dessen die zusammengefassten
Textstücke wiederum als `<item>`s in einer Liste stehen. Das Ziel der
Klammerung steht als reiner Text innerhalb des übergeordneten
`<item>`-Elements.

```
<list>
  <item>
    <list rendition="#rightBraced">
      <item>Element 1 der geklammerten Liste</item><lb/>
      <item>Element 2 der geklammerten Liste</item><lb/>
      <item>Element n der geklammerten Liste</item>
    </list>
  gemeinsamer Textbaustein hinten</item><lb/>
</list><lb/>
```

```
<list>
  <item>gemeinsamer Textbaustein vorn
    <list rendition="#leftBraced">
      <item>Element 1 der geklammerten Liste</item><lb/>
      <item>Element 2 der geklammerten Liste</item><lb/>
      <item>Element n der geklammerten Liste</item><lb/>
    </list>
  </item>
</list><lb/>
```

## Kodierung von Klammerungen in Listen (1)

![](img/gSN1EkEPyA.png)

```
<list>
  <item>
    <list rendition="#rightBraced">
      <item>1. <hi rendition="#aq">Ciliaris.</hi></item><lb/>
      <item>2. <hi rendition="#aq">Orbicularis ſupe-<lb/>rior.</hi></item><lb/>
      <item>3. <hi rendition="#aq">Orbicularis infe-<lb/>rior.</hi></item><lb/>
      <item>4. <hi rendition="#aq">Levator ſeu rectus.</hi></item><lb/>
    </list>
    <hi rendition="#aq">Palpebras<lb/>movent clau-<lb/>dunt &amp; ape-<lb/>riunt.</hi>
  </item>
</list>
```

*Quelle: [Bürger, Peter: Candidatus Chirurgiae. Königsberg, 1692.
[Faksimile 40]](http://www.deutschestextarchiv.de/buerger_candidatus_1692/40)*

## Kodierung von Klammerungen in Listen (2)

![](img/YI4qhVzfvl.png)

```
<list>
  <item>
    <list rendition="#rightBraced">
      <item><hi rendition="#g">John Meſſinger</hi></item><lb/>
      <item><hi rendition="#g">James Lemen</hi> jr.</item>
    </list>
    <hi rendition="#g">St. Clair</hi> (Grafſchaft)
  </item><lb/>
  <item>
    <list rendition="#rightBraced">
      <item><hi rendition="#g">Georg Fiſcher</hi></item><lb/>
      <item><hi rendition="#g">Elias Kent Kone</hi></item>
    </list>
    <hi rendition="#g">Randolph</hi> -
  </item>
</list><lb/>
```

*Quelle: [Ernst, Ferdinand: Bemerkungen auf einer Reise durch das
Innere der vereinigten Staaten von Nord-Amerika im Jahre 1819. Hildesheim, 1820.
[Faksimile 195]](http://www.deutschestextarchiv.de/ernst_nordamerika_1820/195)*


---

## Klammerungen in Tabellen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klTabelle.html](https://www.deutschestextarchiv.de/doku/basisformat/klTabelle.html)

# Klammerungen in Tabellen

Zellen von Tabellen können in der Druckvorlage durch Klammerung
miteinander verbunden und einem gemeinsamen Tabelleneintrag zugeordnet
sein. Solcherlei Klammerungen werden innerhalb des
`<cell>`-Elements ausgedrückt. Den Hinweis auf die
Klammerung erhält dabei der verbindende Tabelleneintrag, der in der Regel
über mehrere Zeilen oder Spalten hinwegreicht.

## Vertikale Klammerung in einer Tabelle:

```
<table>
  <row>
    <cell >[Tabellenwert 1]</cell>
    <cell rows="2" rendition="#leftBraced">[verbindender Tabelleneintrag zu 1 und 2]</cell>
  </row>
  <row>
    <cell>[Tabellenwert 2]</cell>
  </row>
</table>
```

## Horizontale Klammerung in einer Tabelle:

```
<table>
  <row>
    <cell>[Tabellenwert 1]</cell>
    <cell>[Tabellenwert 2]</cell>
  </row>
  <row>
    <cell cols="2" rendition="#topBraced">[verbindender Tabelleneintrag zu 1 und 2]</cell>
  </row>
</table>
```

## Kodierung von Klammerungen in Tabellen

![](img/gA0ctxgCi6.png)

```
<table>
  <row>
    <cell>Nomin.</cell>
    <cell><hi rendition="#i">dobryj</hi></cell>
    <cell>für <hi rendition="#i">dobrŭ-ĭ</hi></cell>
    <cell>grdf.d.endg.</cell>
    <cell><hi rendition="#i">-as-ja-s</hi></cell>
    <cell rendition="#leftBraced" rows="2">ntr. <hi rendition="#i">dobroje,</hi><lb/>
      grdf. d. endg.<lb/><hi rendition="#i">-am-jat</hi> oder<lb/>
      vill. <hi rendition="#i">-at-jat</hi></cell>
  </row><lb/>
  <row>
    <cell>Accus.</cell>
    <cell><hi rendition="#i">dobryj</hi></cell>
    <cell>〃 <hi rendition="#i">dobrŭ-ĭ</hi></cell>
    <cell>〃 〃 〃</cell>
    <cell><hi rendition="#i">-am-jam</hi></cell>
  </row><lb/>
  <row>
    <cell>[...]</cell><lb/>
  </row>
</table>
```

*Quelle: [Schleicher, August: Compendium der
vergleichenden Grammatik der indogermanischen Sprachen. Bd. 2.
Weimar, 1862. [Faksimile 399]](http://www.deutschestextarchiv.de/schleicher_indogermanische02_1862/399)*

Tipp:

Zur Auszeichnung von Tabellen s. Kap. [Tabellen](tabelle.html)


---

## Listenähnliche Klammerungen zusammengehöriger Textpassagen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klText.html](https://www.deutschestextarchiv.de/doku/basisformat/klText.html)

# Listenähnliche Klammerungen zusammengehöriger Textpassagen

Klammerungen können in Textstrukturen auftreten, die nicht genuin Listen
darstellen. Dennoch weisen die zusammengefassten Textstücke selbst eine
listenähnliche Struktur auf. Sie werden daher innerhalb der übergeordneten
Struktur ebenfalls als Listen behandelt.

## Kodierung listenähnlicher Klammerungen im Text (1)

![](img/SUT3ZPohM2.png)

```
<p>Es zerfällt dann die Gleichung (2.) in die folgenden beiden:<lb/>
  <list>
    <item>(3.) 
      <list rendition="#leftBraced">
   <item>
     <formula notation="TeX">0 = 4\pi q' + k^2\Psi' + \frac{d^2\Psi'}{dx^2} + \frac{d^2\Psi'}{dy^2} + \frac{d^2\Psi'}{dz^2}</formula>,
   </item><lb/>
   <item>
     <formula notation="TeX">0 = 4\pi q'' + k^2\Psi'' + \frac{d^2\Psi''}{dx^2} + \frac{d^2\Psi''}{dy^2} + \frac{d^2\Psi''}{dz^2}</formula>,
     </item>
     </list><lb/>
</item></list>
[...]</p>
```

*Quelle: [Helmholtz, Hermann
von: Theorie der Luftschwingungen in Röhren mit
offenen Enden. In: Journal für die reine und
angewandte Mathematik 57 (1860), Heft 1, S. 1-72.
[Faksimile 24]](http://www.deutschestextarchiv.de/helmholtz_luftschwingungen_1860/24)*

## Kodierung listenähnlicher Klammerungen im Text (2)

![](img/Nw3JRMfa_4.png)

```
<l>Dir ſey 
  <list rendition="#leftBraced #rightBraced">
    <item>Lob</item><lb/>
    <item>Danck</item>
  </list> 
geſungen/</l><lb/>
```

*Quelle: [[Canitz, Friedrich
Rudolph Ludwig von]: Neben-Stunden Unterschiedener
Gedichte. [Hrsg. v. Joachim Lange]. Berlin, 1700.
[Faksimile 16]](http://www.deutschestextarchiv.de/canitz_gedichte_1700/16)*


---

## Klammerungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klammerung.html](https://www.deutschestextarchiv.de/doku/basisformat/klammerung.html)

# Klammerungen

## Themen

* [Klammerungen Grundstruktur](klammerungAllg.html)
* [Klammerungen in Listen](klListe.html)
* [Listenähnliche Klammerungen](klText.html)
* [Horizontale Klammerungen](klHorizontal.html)
* [Klammerungen in Tabellen](klTabelle.html)


---

## Grundstruktur der Kodierung von Klammerungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/klammerungAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/klammerungAllg.html)

# Grundstruktur der Kodierung von Klammerungen

Es kann vorkommen, dass Textausschnitte durch zeilenübergreifende Klammerung
miteinander verbunden sind, wodurch deren Zusammengehörigkeit auf einer bestimmten
Ebene angezeigt wird. In diesem Fall wird die Klammerung je nach Kontext für die
Kollektion der geklammerten Textausschnitte oder für das Ziel der Klammerung angezeigt.
Das betreffende Element erhält ein `@rendition`-Attribut, welches folgende Werte
annehmen kann:

* `"#rightBraced"`: Klammerung am rechten Rand des Textes im betreffenden Element
* `"#leftBraced"`: Klammerung am linken Rand des Textes im betreffenden Element
* `"#topBraced"`: Klammerung am oberen Rand des Textes im betreffenden Element
* `"#bottomBraced"`: Klammerung am unteren Rand des Textes im betreffenden Element

Die Richtung, in welche die Klammer jeweils zeigt, wird nicht eigens gekennzeichnet.

In der Regel werden Klammerungen durch Listen dargestellt.

```
<list rendition="#[Klammerungswert]">
```

Lediglich im Drama und in Tabellen können andere Elemente betroffen sein:

Drama:

```
<stage rendition="#[Klammerungswert]">
<speaker rendition="#[Klammerungswert]">
<roleDesc rendition="#[Klammerungswert]">
```

Tabelle:

```
<cell rendition="#[Klammerungswert]">
```


---

## Lebende Kolumnentitel

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/kolumnentitel.html](https://www.deutschestextarchiv.de/doku/basisformat/kolumnentitel.html)

# Lebende Kolumnentitel

Lebende Kolumnentitel befinden sich in den Vorlagen jeweils zu Beginn einer Seite in
der Kopfzeile. Sie werden wie folgt ausgezeichnet:

```
<fw type="header" place="top">[Kolumnentitel]</fw>
```

In der Transkription folgt der Kolumnentitel grundsätzlich auf das `<pb>`-Element,
und somit auf die Angabe der Seitenzahl. Die tatsächliche Position der Seitenzahl
im Verhältnis zum Kolumnentitel bleibt dabei unberücksichtigt. Die Seitenzahl ist
darüber hinaus nicht Bestandteil des Kolumnentitels, sondern des `<pb>`-Elements.

## Kolumnentitel

![](img/z0b3P_yoMC.png)

```
<pb facs="#f0208" n="184"/>
<fw place="top" type="header">Sechsundzwanzigſtes Kapitel: Intrigen.<lb/></fw>
```

*Quelle: [Bismarck, Otto von: Gedanken und Erinnerungen. Bd. 2. Stuttgart, 1898. [Faksimile 208]](http://www.deutschestextarchiv.de/bismarck_erinnerungen02_1898/208)*

Zentrierung, Rechts- oder Linksbündigkeit der Kolumnentitel sowie
Frakturwechsel werden nicht mit angegeben. Sonstige typographische Besonderheiten
(z.B. Fett-, Kursiv-, Gesperrtdruck) werden aus der Vorlage übernommen.


---

## Zeilen- und Spaltenbenennungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/labels.html](https://www.deutschestextarchiv.de/doku/basisformat/labels.html)

# Zeilen- und Spaltenbenennungen

Der Kopf einer Tabellenspalte oder -zeile, welcher die Art der Angaben in der jeweiligen
Spalte/Zeile spezifiziert, kann mittels des Attribut-Wert-Paares
`@role="label"` innerhalb von `<cell>` gekennzeichnet
werden. Diese Angabe ist fakultativ (Level 3).

*Tabelle mit Spaltenrubriken:*

```
<table>
  <head>[ggf. Titel der Tabelle]</head>
  <row>
    <cell role="label">[Kopf der 1. Spalte]</cell>
    <cell role="label">[Kopf der 2. Spalte]</cell>
    <cell role="label">[Kopf der 3. Spalte]</cell>
  </row>
  <row>
    <cell>[Text einer Tabellen-Zelle der 1. Spalte]</cell>
    <cell>[Text einer Tabellen-Zelle der 2. Spalte]</cell>
    <cell>[Text einer Tabellen-Zelle der 3. Spalte]</cell>
  </row>
  ...
</table>
```

*Tabelle mit Zeilenrubriken:*

```
<table>
  <head>[ggf. Titel der Tabelle]</head>
  <row>
    <cell role="label">[Kopf der 1. Zeile]</cell>
    <cell>[Text einer Tabellen-Zelle der 1. Zeile]</cell>
    <cell>[Text einer Tabellen-Zelle der 1. Zeile]</cell>
  </row>
  <row>
    <cell role="label">[Kopf der 2. Zeile]</cell>
    <cell>[Text einer Tabellen-Zelle der 2. Zeile]</cell>
    <cell>[Text einer Tabellen-Zelle der 2. Zeile]</cell>
  </row>
  ...
</table>
```


---

## Grundstruktur der Kodierung von Zeilenumbrüchen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/lbAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/lbAllg.html)

# Grundstruktur der Kodierung von Zeilenumbrüchen

Der Zeilenfall wird aus der Vorlage übernommen. Auch Zeilenumbrüche innerhalb von
Überschriften, Fußnoten, Endnoten, Marginalien etc. werden berücksichtigt.

Jeder Zeilenschluß wird durch das leere Element `<lb/>`
gekennzeichnet. Dieses ist grundsätzlich in keinem Element implizit, sondern wird immer
explizit gesetzt. Allein die Elemente `<pb>`, `<cb>`,
und `<space>` stehen ohne folgendes `<lb>`-Element.

Zeilenumbrüche an Elementenden stehen hinter dem äußersten schließenden Element, jedoch vor
`</front>`, `</body>` (und somit `</floatingText>`),
`</back>` und `</titlePage>`.

```
<lg type="poem">
  <l>[Text Vers a]</l><lb/>
  <l>[Text Vers b]</l>
</lg><lb/>
```

```
<body>
  <div n="1">
    <p>[Text Paragraph a]</p><lb/>
    <p>[Text Paragraph b]</p>
  </div><lb/>
</body>
```


---

## Leerraum

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/leerraum.html](https://www.deutschestextarchiv.de/doku/basisformat/leerraum.html)

# Leerraum

Semantisch bedeutsamer Leerraum in der Vorlage kann mit dem Element
`<space>` ausgezeichnet werden. Das Attribut-Wert-Paar
`@dim="horizontal | vertical"` zeigt an, ob es sich um
horizontalen oder vertikalen Leerraum handelt.

Die Nutzung des Elements `<space>` ist fakultativ (Level 3).

Häufige Anwendungsfälle für `<space>` finden sich z.B. in
[Inhaltsverzeichnissen](inhaltsverzeichnis.html) und
[Listen](liAllg.html).

## Leerraum in Listen

![](img/hGtGNbXQ5B.png)

```
<list>
  <item>1ſter Schlag. Kartoffeln <space dim="horizontal"/> 500°</item><lb/>
  <item>2ter Schlag. Gerſte <space dim="horizontal"/> 400°</item><lb/>
  <item>3ter Schlag. Ma&#x0364;hnklee <space dim="horizontal"/> 325°</item><lb/>
  <item>4ter Schlag. Rocken <space dim="horizontal"/> 299°</item><lb/>
  <item>5ter Schlag. Wicken zu Gru&#x0364;nfutter <space dim="horizontal"/> 525°</item><lb/>
  <item>6ter Schlag. Rocken <space dim="horizontal"/> <hi rendition="#u">500°</hi></item>
</list>
```

*Quelle:
[Thünen,
Johann Heinrich von: Der isolirte Staat in Beziehung auf
Landwirthschaft und Nationalökonomie. Hamburg, 1826. [Faksimile 70]](http://www.deutschestextarchiv.de/thuenen_staat_1826/70)*

## Leerraum in Inhaltsverzeichnissen

![](img/KWBp0ll1jb.png)

```
<div type="content">
  <head>
    <hi rendition="#c #b">Inhalt.</hi><lb/>
  </head>
  <list>
    <item><hi rendition="#right">Seite</hi></item><lb/>
    <item>
      I. Die Geschichte der Zellengranula<space dim="horizontal"/><ref>1</ref>
    </item><lb/>
    <item>
      II. Die Methoden der Granulauntersuchung<space dim="horizontal"/><ref>17</ref>
    </item><lb/>
    <item>
      III. Körner und Fäden der Zellen<space dim="horizontal"/><ref>39</ref>
    </item><lb/>
    <item>
      IV. Die Leber von Rana esculenta<space dim="horizontal"/><ref>56</ref>
    </item><lb/>
    <item>
      V. Die Fettumsetzungen in den Zellen<space dim="horizontal"/><ref>76</ref>
    </item><lb/>
    <item>
      VI. Die Secretionserscheinungen in den Zellen <space dim="horizontal"/><ref>97</ref>
    </item><lb/>
    <item>
      VII. Die Genese der Zelle<space dim="horizontal"/><ref>123</ref>
    </item><lb/>
    <item>
      Erklärungen zu den Tafeln<space dim="horizontal"/><ref>143</ref>
    </item>
  </list>
</div><lb/>
```

*Quelle: [Altmann, Richard: Die
Elementarorganismen und ihre Beziehungen zu den Zellen. Leipzig,
1890. [Faksimile 15]](http://www.deutschestextarchiv.de/altmann_elementarorganismen_1890/15)*

Aber auch im Fließtext können Paragraphen voneinander durch signifikant
mehr Leerraum, als sonst im umgebenden Text üblich, abgetrennt werden.

## Leerraum zwischen Paragraphen

![](img/boerneLeerr02.png)

```
<p>[...]<lb/>
geſchminkte Preßfreiheit zu vertilgen, nun nicht län-<lb/>
ger mehr zweifeln könnte.</p><lb/>
<space dim="vertical"/>
<p>Aus Spanien blüht uns wieder eine neue Hoff-<lb/>
nung entgegen. Es iſt dort in mehreren Provinzen<lb/>
[...]</p>
```

*Quelle: [Börne, Ludwig: Briefe aus Paris. Bd. 6. Paris, 1834. [Faksimile 60]](http://www.deutschestextarchiv.de/boerne_paris06_1834/60)*

**Zum Vergleich:**

![](img/boerneLeerr01.png)

```
<p>[...]<lb/>
freiheit; ſogar einer fürſtlichen verwittweten Unſchuld<lb/>
kann ſie einen böſen Leumund machen.</p><lb/>
<p>Was das elend kranke monarchiſche Prinzip im-<lb/>
merfort an ſich kurirt! wahrhaftig man muß Mitleid<lb/>
[...]</p>
```

*Quelle: [Börne, Ludwig: Briefe aus Paris. Bd. 6. Paris, 1834. [Faksimile 59]](http://www.deutschestextarchiv.de/boerne_paris06_1834/59)*


---

## Legende zu den Übersichten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/legende.html](https://www.deutschestextarchiv.de/doku/basisformat/legende.html)

# Legende zu den Übersichten

## Textbereich: Tagging-Level

**Level 1:** Elemente, die verwendet werden müssen, um das DTA-Basisformat zu erfüllen. Diese Elemente werden konsequent im DTA-Kernkorpus verwendet.

**Level 2:** Elemente, deren Verwendung lt. DTA-Basisformat empfohlen wird, auf die jedoch verzichtet werden kann. Diese Elemente werden in allen Texten des DTA-Kernkorpus verwendet.

**Level 3:** Elemente, die im DTA-Basisformat enthalten sind, jedoch nicht konsequent in den Texten des DTA-Kernkorpus angewandt werden. Die Verwendung dieser Elemente ist fakultativ.

**Level 4:** Elemente, die explizit nicht in das DTA-Basisformat aufgenommen wurden. Sie sollten daher zugunsten der jeweiligen Lösung des DTA-Basisformats vermieden werden.

## Textbereich: Funktionale Kategorien

**citations:** Elemente, die Zitate u. ä. kennzeichnen.

**documentStructure:** Elemente, die Strukturierungen der Vorlage kennzeichnen, welche den äußeren Zugang zur Quelle ermöglichen.

**drama:** Elemente, die dramenspezifische Texteinheiten kennzeichnen.

**editorial:** Elemente, die editorische Eingriffe kennzeichnen.

**floats:** Elemente, die Blöcke kennzeichnen, welche den Fließtext auf Dokument- oder Elementebene unterbrechen.

**letter:** Elemente, die briefspezifische Texteinheiten kennzeichnen.

**phraseStructure:** Elemente, die die Funktion oder das Erscheinungsbild einzelner Wörter oder Phrasen spezifizieren.

**tables:** Elemente, die die Struktur von Tabellen beschreiben.

**textStructure:** Elemente, die die Funktion oder das Erscheinungsbild von Textpassagen innerhalb des Gesamttextes spezifizieren.

**titlepage:** Elemente, die Textabschnitte auf der Titelseite eines Werkes beschreiben.

**verse:** Elemente, die lyrikspezifische Texteinheiten kennzeichnen.

**manuscripts:** Elemente, die für Manuskripte spezifische Merkmale kennzeichnen.

## Textbereich: Generische Attribute

**`@corresp`:** verweist auf korrespondierende interne Elemente oder externe Objekte [`"#[xml:id]", "#[URI]"`]

**`@next`:** verweist auf den Nachfolger in einem mehrteiligen Element [`"#[xml:id]"`]

**`@prev`:** verweist auf den Vorgänger in einem mehrteiligen Element [`"#[xml:id]"`]

**`@rend`:** beschreibt die Art der Hervorhebung einer Zeichenkette

**`@rendition`:** Art der Hervorhebung eines Blocks [`"#aq", "#b", "#blue", "#bottomBraced", "#c", "#et", "#et2", "#et3", "#f", "#fr", "#g", "#i", "#in", "#k", "#larger", "#leftBraced", "#red", "#right", "#rightBraced", "#s", "#smaller", "#sub", "#sup", "#topBraced", "#u", "#uu", "#v"`]

**`@sameAs`:** verweist auf ein Element identischen Inhalts [`"[xml:id]"`]

**`@xml:id`:** Element-ID

**`@xml:lang`:** Sprache-Code (ISO 639-3)

## Header-Bereich: Funktionale Kategorien

**appearance:** Erscheinungsbild des Textes/der Vorlage

**authorTitle:** bibliographische Angaben zu Autor und Titel

**classification:** inhaltliche und formale Einordnung des Textes

**names:** Namen von Personen, Organisationen, Einrichtungen

**publication:** Umstände der Veröffentlichung

**responsibility:** Verantwortlichkeit für Stationen der editorischen Textaufbereitung

**sources:** dem Volltext zugrundeliegende Quellen

**text:** textstrukturierende Elemente für Angaben im TEI Header

## Header-Bereich: Generische Attribute

**`@corresp`:** verweist auf ein korrespondierendes Element ["#[xml:id]"]

**`@xml:id`:** Element-ID

**`@xml:lang`:** Sprache-Code (ISO 639-3)


---

## Leitlinien für die Weiterentwicklung des DTABf

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/leitlinien.html](https://www.deutschestextarchiv.de/doku/basisformat/leitlinien.html)

# Leitlinien für die Weiterentwicklung des DTABf

*Herausgegeben von der [DTABf-Steuerungsgruppe](steuerungsgruppe.html)*

Das DTA-Basisformat (DTABf) stellt ein Format für die TEI-konforme
Textauszeichnung digitaler Volltexte von historischen Drucken mit einer
Erweiterung für Handschriften dar. Mit dem DTABf wollen wir einen
Vorschlag für einen Standard zur Volltext-Aufbereitung im Bereich
(historischer) Textdaten unterbreiten, der die Grundbedürfnisse der
Annotation für verschiedene Disziplinen adressiert. Damit können Texte,
die mit dem Basisformat kompatibel sind, sowohl in das Deutsche
Textarchiv (DTA) einfließen, als auch in anderen Volltextarchiven und
Editionsprojekten leichter nachgenutzt werden.

Das DTABf folgt den
P5-Richtlinien der Text Encoding Initiative (TEI). Da diese Richtlinien
jedoch Lösungen für sämtliche Bedürfnisse bei der Textaufbereitung
anbieten sollen und daher entsprechend vielfältig und umfangreich sind,
bedürfen sie im konkreten Einzelfall einer näheren Spezifizierung. Daher
haben wir aus den P5-Richtlinien für die Textstrukturierung im
DTA-Korpus eine Auswahl an Elementen getroffen (Tagset), die das DTABf
bildet. Dieses Tagset ist mit den P5-Richtlinien der TEI vollständig
konform; auf Erweiterungen durch davon abweichende Elemente wurde
verzichtet.

Ziel des DTABf ist es, eine umfassende
Textaufbereitung zu ermöglichen und dabei gleichzeitig
Variationsspielräume bei der Annotation so einzuschränken, dass die
Interoperabilität aller DTABf-Texte untereinander gewährleistet wird.
Für dieses Ziel stellt die weite zeitliche Erstreckung des DTA-Korpus
einerseits und seine Textsortenvielfalt andererseits eine gute Grundlage
dar, resultiert sie doch u. a. in einer strukturellen Variabilität der
Vorlagen, der mit dem zur Verfügung stehenden Tagset Genüge getan werden
muss. Dennoch werden immer wieder Vorschläge für Weiterentwicklungen des
Formats eingebracht, die z. B. in Textsorten und Überlieferungsmedien
beobachtet wurden, die bislang nicht im Fokus des DTABf
standen.

Die Weiterentwicklung des DTABf und Ergänzung um fehlende
Auszeichnungsmöglichkeiten ist also notwendig. Sie soll allerdings vor
dem geschilderten Hintergrund unter Beachtung einiger Leitlinien
erfolgen:

1. **Für Erweiterungen gilt:** So viel wie nötig, so wenig wie möglich.
   Bei der Erweiterung des Formats um neue Auszeichnungslösungen wird
   darauf geachtet, dass das Format insgesamt möglichst kompakt und
   übersichtlich bleibt. Vor diesem Hintergrund wird jeweils geprüft,
   ob Ergänzungen auf Attributwert-Ebene bereits Abhilfe schaffen. Ist
   dies nicht der Fall, werden entsprechend die Möglichkeiten auf
   Attribut-Ebene und schließlich auf Element-Ebene eruiert.
2. **Ambiguitäten vermeiden:** Auch weiterhin soll bei Ergänzungen zum
   DTABf das Ziel verfolgt werden, die Interoperabilität der
   DTABf-Daten nicht zu gefährden. Dafür wird kritisch untersucht, ob
   ein ‚neues‛ Phänomen möglicherweise durch das vorhandene Tagset mit
   abgedeckt werden kann. Werden Ergänzungen notwendig, wird
   sichergestellt, dass diese nicht zu Unsicherheiten durch alternative
   Annotationsmöglichkeiten führen. Die Vermeidung von Ambiguitäten
   betrifft dabei zweierlei Aspekte: Zum einen sollte es für dasselbe
   Phänomen nur eine mögliche Auszeichnung geben, zum anderen sollte
   dasselbe Tagging nicht gleichzeitig verschiedene Phänomene
   repräsentieren können.
3. **Bestandsübergreifende Relevanz:** Phänomene, für die neue
   Auszeichnungsmöglichkeiten notwendig werden, werden auf verbreitetes
   Vorkommen bzw. projekt- und bestandübergreifende Anwendbarkeit hin
   geprüft. Anwendungsfälle, Auszeichnungslösungen oder Vokabulare, die
   sehr spezifisch für ein Projekt oder eine Fragestellung sind, jedoch
   darüber hinaus voraussichtlich nicht (in der vorgeschlagenen Form)
   genutzt werden, können nicht unterstützt werden.
4. **Allgemeingültigkeit:** Es ist vorgesehen und wird aktiv unterstützt,
   dass das DTABf auch außerhalb des engeren Kontextes des DTA der
   Datenannotation zugrunde gelegt und dabei gegebenenfalls auch um
   projektspezifische bzw. stark fachlich spezialisierte
   Auszeichnungsmöglichkeiten (z. B. historische Maßangaben, Waren und
   Preise, Redewiedergabe) erweitert wird. Solche Erweiterungen sollen
   jedoch nicht in das DTABf zurückfließen. Das DTABf soll hier als
   Startpunkt gelten mit dem Ziel, die Schnittmenge der
   Annotationsbedürfnisse für ganz verschiedene Anwendungsszenarien
   abzubilden.
5. **Dokumentation:** Für das DTABf wird eine umfassende Dokumentation
   angeboten und gepflegt, die unter einer freien Lizenz im DITA-Format
   zur Nachnutzung bereitgestellt wird. Es ist erwünscht, dass diese
   Dokumentation eventuellen weiteren Projektdokumentationen in
   externen Kontexten zugrunde gelegt wird. Darüber hinaus wird
   nachdrücklich empfohlen, Abweichungen vom DTABf, die sich
   möglicherweise aus den Notwendigkeiten des jeweiligen Projekts
   ergeben haben, zu dokumentieren und diese Dokumentation ebenfalls
   öffentlich zugänglich zu machen.
6. **Begrenzung:** Im Fokus des Formats liegen neuzeitliche Drucke und
   Handschriften aus der Zeit vor der Digitalisierung (ca. 1600 bis
   1980). Dabei erweitert das DTABf sein Spektrum gegenüber dem
   ursprünglichen Projektkontext des DTA und DWDS um handschriftliche
   Textsorten sowie um weitere Verwendungsszenarien, z.B. in
   editorischen Kontexten. Das Format unterstützt aktuell primär
   europäische Sprachen- und Schriftsysteme. Eine über diesen
   abgesteckten Rahmen hinausgehende Nutzung ist möglich und kann sich
   anbieten, wird allerdings aktuell nicht aktiv unterstützt.
7. **Pragmatische Edition:** Mit dem DTABf soll es möglich sein, nicht nur
   logische (die Semantik betreffende), sondern auch physische (das
   Layout betreffende) Textstrukturen abzubilden. Dabei wird allerdings
   die Textedition in Form eines diplomatischen Abdrucks nicht
   unterstützt, insofern dieser mimetisch die Vorlage wiederzugeben
   intendiert. So wird z. B. die Auszeichnung von Einrückungen oder
   vertikal gedruckten Textpassagen unterstützt, nicht jedoch die
   Angabe der genauen Tiefe der Einrückung oder des Neigungswinkels
   eines Teiltexts.
8. **Verarbeitung:** Bei Ergänzungen am DTABf wird die Verarbeitbarkeit
   der annotierten Texte besonders berücksichtigt. Eine besondere Rolle
   spielen dabei allgemein z. B. die Vermeidung von Ambiguitäten (Punkt
   2), die Beschränkung des Formats gegenüber neuen
   Auszeichnungsmöglichkeiten (Punkt 3), die Dokumentation und
   technische Spezifikation aller Facetten des Formats (Punkt 5) sowie
   bei konkreten Erweiterungen die Vermeidung von Textinhalt aus der
   Quelle (ausgenommen Nummerierungen) in Attributwerten, entsprechende
   Auszeichnung editorischer Paratexte, Vermeidung offener Wertelisten,
   Unterstützung kanonischer Referenzierungen, Bevorzugung von
   Container- vor Milestone-Elementen etc. Es werden außerdem zusammen
   mit dem Format Verarbeitungsroutinen und Tools zur Unterstützung der
   Auszeichnung angeboten.

## Procedere von Änderungen am DTA-Basisformat

Die Weiterentwicklung des DTABf wird von einer Steuerungsgruppe aus
derzeit 8 Mitgliedern begleitet (s. <http://deutschestextarchiv.de/news/71>).
Anlaufpunkt für Änderungs- und Ergänzungsvorschläge ist das Ticketsystem
der DTABf-Instanz (s. [auf Github](https://github.com/deutschestextarchiv/dtabf/issues)). Über
Vorschläge wird durch die Steuerungsgruppe beraten und schließlich
abgestimmt. Die Annahme eines Änderungsvorschlags
erfordert eine einfache Mehrheit in der Steuerungsgruppe. An der
Abstimmung müssen mindestens 5 Mitglieder der Gruppe beteiligt sein, um
das Quorum zu erreichen. Abgestimmt werden kann mit “Annahme der
Änderung”, “Ablehnung der Änderung” oder Enthaltung.


---

## Grundstruktur der Kodierung von Listen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/liAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/liAllg.html)

# Grundstruktur der Kodierung von Listen

Listen werden mittels des `<list>`-Elements ausgezeichnet. Jeder
Listenpunkt wird mittels `<item>[...]</item>` umschlossen. Trägt
die Liste einen Titel, so wird dieser durch das `<head>`-Element als
solcher gekennzeichnet.

```
<list>
  <head>[Titel der Liste]</head><!-- sofern vorhanden -->
  <item>[Inhalt eines Listenpunkts]</item>
  <item>[Inhalt eines Listenpunkts]</item>
</list>
```

Nummerierungen von Listenpunkten werden innerhalb von
`<list>[...]</list>` (d.h. auf Textebene) realisiert und nicht
gesondert ausgezeichnet.

```
<list>
  <item>1. [Inhalt des ersten Listenpunkts]</item>
  <item>2. [Inhalt des zweiten Listenpunkts]</item>
  ...
  <item>[n]. [Inhalt des n-ten Listenpunkts]</item>
</list>
```

## Kodierung von Listen

![](img/UK36EOOiL3.png)

```
<list>
  <item>[...]</item>
  <item>
    <hi rendition="#aq">s)</hi>Der erſte Stein <hi rendition="#aq">a</hi>, 
    auf dem Gewölbefuß liegend, heißt: <hi rendition="#g">An-<lb/>
    fänger</hi>- oder <hi rendition="#g">Kämpferſtein</hi>.
  </item><lb/>
  <item>
    <hi rendition="#aq">t)</hi>Der Stein <hi rendition="#aq">t</hi> 
    in der oberſten Spitze des Gewölbes heißt:<lb/>
    <hi rendition="#g">Schlußſtein</hi>.
  </item><lb/>
  <item>
    <hi rendition="#aq">u)</hi>Jede Hälfte eines Gewölbes, 
    welche durch eine verticale, durch<lb/>
    die Scheitellinie gelegte Ebene gebildet wird, 
    heißt: <hi rendition="#g">Gewölbe-<lb/>
    ſchenkel</hi>; dieſelben ſind in der Regel ſich gleich, 
    bei einhüftigen Ge-<lb/>
    wölben (Fig. 256) reſp. Bögen aber ungleich.
  </item><lb/>
  <item>[...]</item>
</list><lb/>
```

*Quelle:
[Wanderley,
Germano: Handbuch der Bauconstruktionslehre. 2. Aufl. Bd. 2. Die
Constructionen in Stein. Leipzig, 1878. [Faksimile 267]](http://www.deutschestextarchiv.de/wanderley_bauconstructionslehre02_1878/267)*

Besteht eine Liste aus Einträgen mit zugehörigen Werten,
die durch einen Abstandhalter (z.B. einen Leerraum oder eine
gepunktete Linie) voneinander getrennt sind, so wird der Abstand
mittels `<space dim="horizontal"/>` angezeigt.

## Umgang mit Abstandhaltern in Listen

![](img/hGtGNbXQ5B.png)

```
<list>
  <item>1ſter Schlag. Kartoffeln <space dim="horizontal"/> 500°</item><lb/>
  <item>2ter Schlag. Gerſte <space dim="horizontal"/> 400°</item><lb/>
  <item>3ter Schlag. Ma&#x0364;hnklee <space dim="horizontal"/> 325°</item><lb/>
  <item>4ter Schlag. Rocken <space dim="horizontal"/> 299°</item><lb/>
  <item>5ter Schlag. Wicken zu Gru&#x0364;nfutter <space dim="horizontal"/> 525°</item><lb/>
  <item>6ter Schlag. Rocken <space dim="horizontal"/> <hi rendition="#u">500°</hi></item>
</list>
```

*Quelle:
[Thünen,
Johann Heinrich von: Der isolirte Staat in Beziehung auf
Landwirthschaft und Nationalökonomie. Hamburg, 1826. [Faksimile 70]](http://www.deutschestextarchiv.de/thuenen_staat_1826/70)*

Ein typischer Anwendungsfall für solcherlei Listen sind [Inhaltsverzeichnisse](inhaltsverzeichnis.html).

Klammerungen innerhalb von `Listen` werden mittels des Attribut-Wert-Paares
`@rendition="#rightBraced|#leftBraced|#topBraced|#bottomBraced"`
ausgezeichnet (vgl. Kap. [Klammerungen](klammerung.html)).


---

## Verschachtelte Listen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/liVerschachtelt.html](https://www.deutschestextarchiv.de/doku/basisformat/liVerschachtelt.html)

# Verschachtelte Listen

Listenelemente können verschachtelt werden:

```
<list>
  <head>[Titel der Liste]</head><!-- sofern vorhanden -->
  <item>[ggf. Inhalt eines übergeordneten Listenpunkts]
    <list>
      <item>[Inhalt eines Listenpunkts]</item>
      <item>[Inhalt eines Listenpunkts]</item>
    </list>
  </item>
</list>
```

## Kodierung verschachtelter Listen

![](img/i5oVj5kLXH.png)

```
<list>
 <item>c) In dem Bergamtsrevier Naila:<lb/>
 <list>
  <item>
   1. Der Dorschenhammer oder das obere Schauensteiner Hammer-<lb/>
   werk an der Selbitz war ein Stabfeuer, das sein Roheisen<lb/>
   von dem Hochofen zu Thiemitz, an dem es zur Hälfte be-<lb/>
   teiligt war, erhielt.
  </item><lb/>
  <item>
    2. Der Kleinschmiedhammer oder untere Schauensteinerhammer<lb/>
    an der Selbitz erhielt sein Roheisen von dem Klingsporner<lb/>
    Werk.
  </item><lb/>
 </list>
 </item>
</list>
```

*Quelle: [Beck, Ludwig: Die Geschichte des Eisens. Bd. 3: Das
XVIII. Jahrhundert. Braunschweig, 1897. [Faksimile 841]](http://www.deutschestextarchiv.de/beck_eisen03_1897/841)*


---

## Listen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/liste.html](https://www.deutschestextarchiv.de/doku/basisformat/liste.html)

# Listen

## Themen

* [Listen Grundstruktur](liAllg.html)
* [Verschachtelte Listen](liVerschachtelt.html)


---

## Auszeichnung von Manuskripten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/manuskript.html](https://www.deutschestextarchiv.de/doku/basisformat/manuskript.html)

# Auszeichnung von Manuskripten

## Themen

* [Manuskripte Allgemeines](msAllg.html)
* [Kapitelstruktur](msKapitel.html)
* [Textänderungen Autor](msAenderungen.html)
* [Einweisungszeichen](msEinweisung.html)
* [Anmerkungen Autor](msAnmerkungen.html)
* [Platzhalter](msPlatzhalter.html)
* [Editorisches Inventar](msEditorBearbeitung.html)
* [Seiten- und Blattnummerierung](msFoliierung.html)
* [Bibliotheksstempel](msStamp.html)
* [Besonderheiten Metadaten](msMetadata.html)


---

## Randbemerkungen (Marginalien)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/marginalie.html](https://www.deutschestextarchiv.de/doku/basisformat/marginalie.html)

# Randbemerkungen (Marginalien)

Für die Auszeichnung von Marginalien wird ebenso wie für Fuß- und
Endnoten das Element `<note>` verwendet. Das
Attribut `@place` kann die Werte
`right` und `left` annehmen, welche
die Position der Marginalie in Bezug auf den Textbereich
spezifizieren.

```
<note place="right">[rechts vom Text stehende Marginalien]</note>
<note place="left">[links vom Text stehende Marginalien]</note>
```

Rechts vom Text (`@place="right"`) stehende
Marginalien werden unmittelbar nach der Zeile, auf deren Höhe sie
beginnen, transkribiert, links vom Text
(`@place="left"`) stehende Marginalien unmittelbar
vor der Zeile, auf deren Höhe sie beginnen.

## Kodierung von Marginalien am linken Rand

![](img/eOZw1swX4p.png)

```
<p>Der folgende Kaiser, 
  <hi rendition="#k">Yuṅ-tšin</hi>, vertrieb bei seiner Thron-<lb/>
    <note place="left">
      1723.
    </note>
  besteigung 1723 alle Missionare als Ruhestörer. Einige hielten sich<lb/>
  [...]
</p>
```

*Quelle: [[Berg, Albert]: Die preussische
Expedition nach Ost-Asien. Bd. 3. Berlin, 1873. [Faksimile
36]](http://www.deutschestextarchiv.de/berg_ostasien03_1873/36)*

## Kodierung von Marginalien am rechten Rand

![](img/Io0IuZbxlS.png)

```
<p>[...]<lb/>
  Die Todtenopfer und andere Gebräuche, welche er als bürgerliche<lb/>
  duldete, wurden von den Dominicanern als götzendienerisch ver-<lb/>
  dammt und allen chinesischen Christen unter Androhung der Höllen-
    <note place="right">
      1644.
    </note><lb/>
  strafen verboten. Papst Innocenz X. bestätigte dieses Urtheil, das
    <note place="right">
      1655.
    </note><lb/>
  Alexander VII. auf Vorstellung der Jesuiten wieder aufhob. Die<lb/>
  [...]
</p>
```

*Quelle: [[Berg, Albert]: Die preussische
Expedition nach Ost-Asien. Bd. 3. Berlin, 1873. [Faksimile
35]](http://www.deutschestextarchiv.de/berg_ostasien03_1873/35)*

Steht eine Marginalie am linken Rand direkt am Beginn eines neuen
Paragraphen, so wird sie mit innerhalb des
`<p>`-Elements wiedergegeben.

## Kodierung von Marginalien am Beginn eines neuen Paragraphen

![](img/DdYcYPlXK1.png)

```
<p>
  <note place="left">
    Vnſer ge-<lb/>
    rechtig-<lb/>
    keit iſt auf<lb/>
    keine Cre-<lb/>
    atur ge-<lb/>
    gru&#x0364;ndet/<lb/>
    ſondern<lb/>
    auff Gott.
  </note> 5. Vnſere gerechtigkeit kan auff kei-<lb/>
  nen Engel gebawet werden. Dann es iſt<lb/>
  [...]
</p>
```

*Quelle: [Arndt, Johann: Vom wahren
Christenthumb. Bd. 2. Magdeburg, 1610. [Faksimile
64]](http://www.deutschestextarchiv.de/arndt_christentum02_1610/64)*

Ist eine Marginalie in den Text eingewiesen, so besteht die
Möglichkeit (Level 3), diesen Verweis analog zum Verfahren bei der
[Auszeichnung von Endnoten](endnote.html) wiederzugeben. Die Marginalie wird
dabei wie oben beschrieben transkribiert. Im
`<note>`-Element, das die Marginalie
umschließt, steht ein `@n`-Attribut, welches als Wert
das Referenzzeichen der Marginalie erhält. Das korrespondierende
Referenzzeichen im Text wird mit einem untypisierten
`<note>`-Element umschlossen. Beide
`<note>`-Elemente werden mittels
`@xml:id` und `@corresp` miteinander
verknüpft (vgl. dazu Kap. [4.2.2](parallelePassagen.html)).

```
<p>
  [Text Zeilenbeginn]
    <note n="[Referenz]" xml:id="[ID-Referenz]" corresp="#[ID-Marginalie]"/>
  [Text Zeilenschluss]
    <note place="right" n="[Referenz]" xml:id="[ID-Marginalie]" corresp="#[ID-Referenz]">[Marginalie]</note>
```


---

## Umgang mit Abkürzungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAbkuerzungen.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAbkuerzungen.html)

# Umgang mit Abkürzungen

Abkürzungen im Titel werden grundsätzlich nicht aufgelöst. Eine Ausnahme bildet
der Kürzungsstrich, z.B. über Nasal. Dieser wird stillschweigend expandiert.


---

## Grundstruktur der Kodierung von Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAllg.html)

# Grundstruktur der Kodierung von Metadaten

Die Metadaten werden im Element `<teiHeader>` erfasst. Dabei umfassen die Metadaten im TEI-Header folgende Angaben:

* die Titel- und Quellenangaben zur vorliegenden Textausgabe (innerhalb
  von `<fileDesc>`; siehe dazu Kap. [Bibliographische
  Angaben](mdBiblAngaben.html)),
* Angaben zu den editorischen Richtlinien, welche der Ausgabe zugrunde
  liegen (innerhalb von `<encodingDesc>`;
  siehe dazu Kap. [Editorische Richtlinien](mdEncodingDesc.html)) sowie
* erste inhaltliche Angaben zum Text (innerhalb von `<profileDesc>`;
  siehe dazu Kap. [Dokumentklassifikationen](mdProfileDesc.html)).

```
<teiHeader>
  <fileDesc>[Bibliographische Angaben]</fileDesc>
  <encodingDesc>[Editorische Richtlinien]</encodingDesc>
  <profileDesc>[Dokumentklassifikationen]</profileDesc>
</teiHeader>
```


---

## Auflage

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAuflage.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAuflage.html)

# Auflage

Nähere Angaben zur Auflage eines Werkes auf dessen Titelseite werden in den ausführlichen
Titeldaten entsprechend der Vorlage wiedergegeben. In der Kurztitelangabe steht verkürzt
"`[Nummer]. Aufl.`".

## Kodierung der Auflage

*Siehe:* <http://www.deutschestextarchiv.de/wanderley_bauconstructionslehre01_1877>


---

## Auszeichnung der Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAuszeichnung.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAuszeichnung.html)

# Auszeichnung der Metadaten

Im folgenden Kapitel werden die Richtlinien für die Auszeichnung der Metadaten beschrieben.

## Themen

* [Metadaten Grundstruktur](mdAllg.html)
* [File Description](mdBiblAngaben.html)
* [Encoding Description](mdEncodingDesc.html)
* [Profile Description](mdProfileDesc.html)
* [Überblick TEI-Header](mdUeberblick.html)


---

## Die Unterstrukturierung der Elemente //author und //editor

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAuthorEditor.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAuthorEditor.html)

# Die Unterstrukturierung der Elemente `//author` und `//editor`

Die Angabe des Autors/der Autoren eines Textes erfolgt im Element `<author>` des
*Title Statements*, welches sowohl in der [*File Description*](mdTitleStmt.html) als
auch im [`<biblFull>`-Element der *Source Description*](mdSdTitleStmt.html)
stehen kann. Im Falle mehrerer Autoren wird das `<author>`-Element mehrfach verwendet.
Gleiches gilt für das Element `<editor>` zur Angabe des Herausgebers eines Textes.

Der Name des Autors/Herausgebers/Übersetzers steht jeweils im Unterelement `<persName>` des
`<author>`- bzw. `<editor>`-Elements (zur weiteren Strukturierung des
Elements `<persName>` siehe Kap. [Die Unterstrukturierung des
Elements `<persName>`](mdPersName.html)).

*Strukturierung des <author>-Elements:*

```
<author>
  <persName>[Name des Autors]</persName>
</author>
```

*Strukturierung des <editor>-Elements der File Description*

```
<editor corresp="#[XML-ID des Publication Statements]">
  <persName>[Name des Herausgebers der DTA-Ausgabe in der File Description]</persName>
</editor>
```

*Strukturierung des <editor>-Elements der Source Description*

```
<editor>
  <persName>[Name des Herausgebers der Quelle]</persName>
</editor>
<editor role="translator">
  <persName>[Name des Übersetzers der Vorlage zur Quelle]</persName>
</editor>
```


---

## Autor/Herausgeber/Übersetzer

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdAutorHrsgUebers.html](https://www.deutschestextarchiv.de/doku/basisformat/mdAutorHrsgUebers.html)

# Autor/Herausgeber/Übersetzer

Angaben zum Autor, Herausgeber oder Übersetzer eines Werks werden ungeachtet der Vorlage
entsprechend der Ansetzungsform der GND wiedergegeben. Ist der Name nicht in der GND
nachweisbar, so wird dieser vorlagengetreu übernommen.

HINWEIS:

Zur Strukturierung von Personennamen
s. Kap. [Personal Name](mdPersName.html).


---

## Band

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdBand.html](https://www.deutschestextarchiv.de/doku/basisformat/mdBand.html)

# Band

Die Bandangabe eines Werkes auf dessen Titelseiten wird in den ausführlichen Titeldaten
entsprechend der Vorlage wiedergegeben.

In der Kurztitelangabe steht verkürzt "`Bd. [Nummer]`". Dabei steht grundsätzlich
"`Bd.`", ungeachtet der Bezeichnung des Bandes (z.B. als "Heft" oder "Teil") in der
Vorlage.

## Bandangabe im Kurztitel

*Siehe:* <http://www.deutschestextarchiv.de/euler_algebra02_1770>


---

## Besonderheiten der Metadatenerfassung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdBesonderheitenErfassung.html](https://www.deutschestextarchiv.de/doku/basisformat/mdBesonderheitenErfassung.html)

# Besonderheiten der Metadatenerfassung

Im Folgenden werden besondere Festlegungen zur Metadatenerfassung
erläutert, die für die Erstellung DTABf-konformer Metadatensätze
relevant sind.

## Themen

* [Titelangaben](mdTitelangaben.html)
* [Autor/Herausgeber/Übersetzer](mdAutorHrsgUebers.html)
* [Erscheinungsort](mdErscheinungsort.html)
* [Verlag](mdVerlag.html)
* [Auflage](mdAuflage.html)
* [Band](mdBand.html)
* [Kurztitelaufnahme](mdKtAufnahme.html)


---

## Bibliographische Angaben: Die File Description (//fileDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdBiblAngaben.html](https://www.deutschestextarchiv.de/doku/basisformat/mdBiblAngaben.html)

# Bibliographische Angaben: Die *File Description* `(//fileDesc)`

## Themen

* [File Description Grundstruktur](mdFileDescAllg.html)
* [Title Statement](mdTitleStmt.html)
* [Edition Statement](mdEditionStmt.html)
* [Extent](mdExtent.html)
* [Publication Statement](mdPublicationStmt.html)
* [Notes Statement](mdNotesStmt.html)
* [Source Description](mdSourceDesc.html)


---

## Umgang mit Sonderzeichen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdDiakritika.html](https://www.deutschestextarchiv.de/doku/basisformat/mdDiakritika.html)

# Umgang mit Sonderzeichen

Diakritika, Ligaturen und weitere Sonderzeichen, die sich auf eine eindeutige moderne Entsprechung abbilden lassen,
werden in den Metadaten entsprechend normalisiert. Dies betrifft z.B. die folgenden Zeichen:

| Historische Schreibung | Umsetzung als |
| --- | --- |
| aͤ, oͤ, uͤ | ä, ö, ü |
| ſ | s |
| ſs, ſz | ß |
| Ꝛ, ꝛ | R, r |

Sonderzeichen, für die keine eindeutige Entsprechung gefunden werden kann
(z.B. kontextbezogen ů) werden nicht normalisiert. In diesem Fall wird das
entsprechende Unicode-Zeichen gesetzt.


---

## Umgang mit Druckfehlern und ungewöhnlichen Schreibungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdDruckfehler.html](https://www.deutschestextarchiv.de/doku/basisformat/mdDruckfehler.html)

# Umgang mit Druckfehlern und ungewöhnlichen Schreibungen

Sämtliche eindeutigen Druckfehler in den Titelangaben der Vorlage werden stillschweigend
korrigiert.

Ungewöhnliche, aber historisch mögliche Schreibungen werden hingegen unverfälscht aus
der Vorlage übernommen. Sie werden nicht gesondert gekennzeichnet (wie z.B. durch einen
(sic!)-Vermerk im Anschluss an das betreffende Wort.


---

## Hinweise zur Art der vorliegenden Textausgabe (//fileDesc/editionStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdEditionStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdEditionStmt.html)

# Hinweise zur Art der vorliegenden Textausgabe `(//fileDesc/editionStmt)`

Das *Edition Statement* beinhaltet im Unterelement `<edition>`
die Angabe zur Art der vorliegenden DTA-Publikation des jeweiligen Werks.

```
<editionStmt>
  <edition>[Art der DTA-Ausgabe, d.i. "Vollständige digitalisierte Ausgabe"]</edition>
</editionStmt>
```


---

## Editorische Richtlinien (//encodingDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdEncodingDesc.html](https://www.deutschestextarchiv.de/doku/basisformat/mdEncodingDesc.html)

# Editorische Richtlinien `(//encodingDesc)`

Hinweise zu den editorischen Richtlinien, die der DTA-Textausgabe zugrunde liegen, werden in der
*Encoding Description* (`<encodingDesc>`) festgehalten.

Dabei beinhaltet das
Unterelement *Editorial Description* Angaben zur Erfassungsart für den jeweiligen Text sowie
zum Grad der Konformität des Textes mit den DTA-Richtlinien ([DTA-Transkriptionsrichtlinien](http://www.deutschestextarchiv.de/doku/richtlinien) und
[DTA-Basisformat](http://www.deutschestextarchiv.de/doku/basisformat)).

Das Unterelement *Tags Declaration* enthält in mehreren `<rendition>`-Elementen
die Angabe, wie die `@rendition`-Werte des TEI-Textes beim Rendering in CSS aufgelöst
werden sollen.

```
<encodingDesc>
  <editorialDecl>
    <p>[Angaben zu den Transkriptions- und Annotationsrichtlinien]</p>
    <p>[weitere Angaben zu den Transkriptions- und Annotationsrichtlinien]</p>
  </editorialDecl>
  <rendition scheme="css" xml:id="[@rendition-Wert]">[CSS-Entsprechung]</rendition>
</encodingDesc>
```

Achtung:

Die CSS-Entsprechungen, die im DTA für die jeweiligen `@rendition`-Werte genutzt wurden,
sind im Kapitel [Typographische Besonderheiten - Richtlinien der Kodierung](typogrAllg.html)
dokumentiert.


---

## Erscheinungsort

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdErscheinungsort.html](https://www.deutschestextarchiv.de/doku/basisformat/mdErscheinungsort.html)

# Erscheinungsort

Erscheinungsorte, deren Name und Status unverändert geblieben sind, werden entsprechend
der heute gängigen Schreibung wiedergegeben. Eine Orientierung bilden dabei die Ansetzungsformen
im folgenden Verzeichnis:
Druckorte des 16. bis 19. Jahrhunderts. Ansetzungs- und Verweisungsformen. Erarbeitet von der
Bayerischen Staatsbibliothek. Wiesbaden: Reichert, 1991.

Namenszusätze stehen jedoch grundsätzlich in runden Klammern im Anschluss an den Ortsnamen.

## Namenszusätze in Erscheinungsorten

Frankfurth a. Mayn → Frankfurt (Main)

Freiburg i. Br. → Freiburg (Breisgau)

Latinisierte Ortsnamen werden entsprechend der heutigen Form wiedergegeben.

## Latinisierte Ortsnamen

Argentoratum → Straßburg

Historische Ortsnamen, die heutzutage keine äquivalente Entsprechung haben, weil (a) der Ort
in der historischen Form nicht mehr existiert, oder (b) der Name des Orts sich verändert hat,
werden entsprechend der historischen Schreibung der Quelle wiedergegeben. Namenszusätze stehen
in runden Klammern im Anschluss an den Ortsnamen.

## Historische Ortsnamen

Cölln (Spree)


---

## Die Umfangsangabe innerhalb der File Description (//fileDesc/extent)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdExtent.html](https://www.deutschestextarchiv.de/doku/basisformat/mdExtent.html)

# Die Umfangsangabe innerhalb der *File Description* `(//fileDesc/extent)`

Ein `<extent>`-Element innerhalb der *File Description* dient der Angabe des Umfangs des DTA-Volltextes. Der Umfang wird in mehreren
`<measure>`-Elementen in unterschiedlichen Einheiten (Faksimile-Dateien, Tokens, Types, Zeichen) angegeben.

```
<extent>
  <measure type="images">[Umfang: Anzahl der Faksimile-Dateien]</measure>
  <measure type="tokens">[Umfang: Anzahl der Tokens]</measure>
  <measure type="types">[Umfang: Anzahl der Types]</measure>
  <measure type="characters">[Umfang: Anzahl der Zeichen]</measure>
</extent>
```


---

## Grundstruktur der File Description (//fileDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdFileDescAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdFileDescAllg.html)

# Grundstruktur der *File Description* `(//fileDesc)`

Die bibliographischen Angaben zum DTA-Volltext und der jeweils zugrunde liegenden Quelle werden in
der *File Description* (`<fileDesc>`) zusammengefasst.

```
<fileDesc>
  <titleStmt>[Titelangaben zur DTA-Ausgabe]</titleStmt>
  <editionStmt>[Art der DTA-Ausgabe]</editionStmt>
  <extent>[Umfangsangabe]</extent>
  <publicationStmt>[Spezifika der DTA-Ausgabe]</publicationStmt>
  <sourceDesc>[Angaben zur Vorlage des DTA-Volltextes]</sourceDesc>
</fileDesc>
```


---

## Kurztitelaufnahme

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdKtAufnahme.html](https://www.deutschestextarchiv.de/doku/basisformat/mdKtAufnahme.html)

# Kurztitelaufnahme

Die Titelangabe innerhalb der Kurztitelaufnahme orientiert sich an der Vorlage. Sie ist
jedoch in ihrer Länge möglichst zu begrenzen, um die schnelle Erfassung der bibliographischen
Angabe zu ermöglichen. Die Titelangabe wird ungeachtet der Vorlage grundsätzlich mit einem
Großbuchstaben eingeleitet.

## Überblick über Kurztitelaufnahmen nach Dokumentsorte

Monographien:
:   *Autorname*, *Autorvorname*: *Kurztitel*. *Druckort*, *Jahr*.

Band einer mehrbändigen Ausgabe:
:   *Autorname*, *Autorvorname*: *Kurztitel*. Bd. *Bandnummer*: *ggf. Bandtitel*. *Druckort*, *Jahr*.

Band einer Reihe:
:   *Autorname*, *Autorvorname*: *Kurztitel*. *Druckort*, *Jahr* (= *Reihentitel*, Bd. *Bandnummer*).

Unselbständige Schrift in einer Zeitschrift/Zeitung:
:   *Autorname*, *Autorvorname*: *Kurztitel*. In: *Kurztitel der Zeitschrift/Zeitung Nummer* (*Jahr*), S. *Seitenangabe*.

Unselbständige Schrift in einem Sammelband:
:   *Autorname*, *Autorvorname*: *Kurztitel*. In: *Kurztitel des Sammelbandes*. *Druckort*, *Jahr*, S. *Seitenangabe*.

Kapitel einer Monographie:
:   *Autorname*, *Autorvorname*: *Kurztitel*. In: *Kurztitel der Monographie*. *Druckort*, *Jahr*, S. *Seitenangabe*.

## Spezialfälle

Spätere Ausgabe:
:   *Autorname*, *Autorvorname*: *Kurztitel*. *Nummer der Auflage*. Aufl. *Druckort*, *Jahr*.

Mehrere Verfasser:
:   *Autorname*, *Autorvorname*; *Autorname*, *Autorvorname*: *Kurztitel*. *Druckort*, *Jahr*.

Verfasser mit Adelsprädikat:
:   *Autorname*, *Autorvorname*
    *Adelsprädikat*: *Kurztitel*. *Druckort*, *Jahr*.

Unbekannter Verfasser:
:   [N. N.]: *Kurztitel*. *Druckort*, *Jahr*.
:   ➔ *Für mehr Informationen siehe Kapitel: [Umgang mit unvollständigen Angaben](mdUnvollstAngaben.html).*

Mehrere Erscheinungsorte:
:   *Autorname*, *Autorvorname*: *Kurztitel*. *Druckort* u. a., *Jahr*.

Unbekannter Erscheinungsort:
:   *Autorname*, *Autorvorname*: *Kurztitel*. [s. l.], *Jahr*.
:   ➔ *Für mehr Informationen siehe Kapitel: [Umgang mit unvollständigen Angaben](mdUnvollstAngaben.html).*

Herausgeber, statt Autor:
:   *Herausgebername*, *Herausgebervorname* (Hrsg.): *Kurztitel*. *Druckort*, *Jahr*.

Herausgeber, abweichend vom Autor:
:   *Autorname*, *Autorvorname*: *Kurztitel*. Hrsg. v. *Herausgebervorname Herausgebername*. *Druckort*, *Jahr*.

Übersetzer:
:   *Autorname*, *Autorvorname*: *Kurztitel*. Übers. v. *Übersetzervorname Übersetzername*. *Druckort*, *Jahr*.


---

## Lizenzangaben (//availability/licence)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdLicense.html](https://www.deutschestextarchiv.de/doku/basisformat/mdLicense.html)

# Lizenzangaben (//availability/licence)

Lizenzangaben stehen in einzelnen `<availability>`-Elementen innerhalb des *Publication Statements*,
die ihrerseits jeweils genau ein Unterelement `<licence>` erhalten. Das `@target`-Attribut des
`<licence>`-Elements enthält als Wert eine URL, die zu einer Spezifikation der angegebenen Lizenz führt.
In einem `<p>`-Element innerhalb von `<licence>` sind weitere natürlichsprachliche
Angaben zur Lizenz möglich.

```
<availability>
  <licence target="[URL zum Lizenztext]">
    <p>[Beschreibungstext zur Lizenz]</p>
  </licence>
</availability>
```

## Lizenzangaben

```
<availability>
  <licence target="http://creativecommons.org/licenses/by-sa/2.0/de/">
    <p>Distributed under the Creative Commons Attribution-ShareAlike 2.0 Generic (German) License.</p>
  </licence>
</availability>
```

## Mehrere Lizenzangaben im teiHeader

In den `<availability>`-Elementen des *Publication Statements* werden sowohl die Lizenzen sämtlicher
Bild- und Textvorlagen der DTA-Publikation als auch die Lizenz der DTA-Textedition selbst angegeben.

Dabei erhält jedes `<availability>`-Element eine
eindeutige `@xml:id`. Über ein
`@corresp`-Attribut wird es mit dem Element
verbunden, welches Angaben zu dem jeweiligen Lizenzträger
enthält. Dies kann einerseits ein *Responsibility
Statement* (`<respStmt>`) sein, welches
Angaben zu zugrundeliegenden Textdigitalisaten enthält, oder
eine *Manuscript Description*
(`<msDesc>`), welche Angaben zu
Bildvorlagen enthält. (Zum *Responsibility Statement* s.
Kap. [Umgang mit externen
Quellen](mdRespStmt.html); zur *Manuscript Description* s. Kap. [Angaben zum Aufbewahrungsort der
Quelle](mdSdMsDesc.html).)

```
<teiHeader>
  <fileDesc>
    <titleStmt>
      [...]
      <respStmt xml:id="tq-1" corresp="#availability-tq-1">[Angaben zur Textvorlage]</respStmt>
    </titleStmt>
    [...]
    <publicationStmt>
      [...]
      <availability xml:id="availability-tq-1" corresp="#tq-1"> <!-- Lizenz einer Textquelle -->
        <licence target="[URL Lizenztext]">
          <p>[Beschreibungstext zur Lizenz der Textquelle]</p>
        </licence>
      </availability>
      <availability xml:id="availability-bq-1" corresp="#bq-1"> <!-- Lizenz einer Bildquelle -->
        <licence target="[URL Lizenz Bildquelle]">
          <p>[Beschreibungstext zur Lizenz der Bildquelle]</p>
        </licence>
      </availability>
    </publicationStmt>
    <sourceDesc>
      [...]
      <msDesc xml:id="bq-1" corresp="#availability-bq-1">
        [nähere Angaben zur Bildquelle]
      </msDesc>
    </sourceDesc>
  </fileDesc>
  [...]
</teiHeader>
```


---

## Normalisierungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdNormalisierungen.html](https://www.deutschestextarchiv.de/doku/basisformat/mdNormalisierungen.html)

# Normalisierungen

Bei der Aufnahme von Titeldaten entsprechend der Vorlage sind ausgewählte
Normalisierungen möglich.

## Themen

* [Umgang mit typographischen Hervorhebungen](mdTypographHervorhebungen.html)
* [Umgang mit Diakritika](mdDiakritika.html)
* [Umgang mit Abkürzungen](mdAbkuerzungen.html)
* [Umgang mit unvollständigen Angaben](mdUnvollstAngaben.html)
* [Umgang mit verfälschten/verschleierten Angaben](mdVerfaelschteAngaben.html)
* [Umgang mit Druckfehlern und ungewöhnlichen Schreibungen](mdDruckfehler.html)


---

## Zusatzinformationen zum Dokument (//fileDesc/notesStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdNotesStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdNotesStmt.html)

# Zusatzinformationen zum Dokument (//fileDesc/notesStmt)

Weitere, über die im DTABf vorgesehene Metadatenerfassung hinausgehende Informationen zu dem
edierten Dokument können innerhalb der `<fileDesc>` in einem eigenen
`<notesStmt>`-Element angebracht werden. Dabei erhält das
`<notesStmt>` ein Unterelement `<note>` mit dem Attribut-Wert-Paar
`@type="remarkDocument"`.

```
<notesStmt>
  <note type="remarkDocument">[Zusatzinformationen zum Dokument]</note>
</notesStmt>
  
```


---

## Die Unterstrukturierung des Elements //persName

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdPersName.html](https://www.deutschestextarchiv.de/doku/basisformat/mdPersName.html)

# Die Unterstrukturierung des Elements `//persName`

Der Name einer Person wird in einem `<persName>`-Element festgehalten. Das `@ref`-Attribut
in `<persName>` ermöglicht den Verweis (qua URL) auf eine Ressource, die zusätzliche Angaben zu
der betreffenden Person enthält, etwa auf den Datensatz zu dieser Person in der
[Gemeinsamen Normdatei (GND)](http://www.dnb.de/DE/Standardisierung/GND/gnd_node.html). Konnte ein Name
in der GND nicht nachgewiesen werden, so erhält das `@ref`-Attribut des `<persName>`-Elements
den Wert `"nognd"`.

Folgende Unterelemente des Elements `<persName>` sind möglich:

| Element | Funktion |
| --- | --- |
| `surname` | Familienname |
| `forename` | Vorname |
| `nameLink` | Namenszusatz, z.B. Adelsprädikat |
| `genName` | Generation |
| `addName` | ggf. Pseudonym oder sonstiger zusätzlicher Name |
| `roleName` | staatstragende Funktion/offizieller Titel der Person |

Achtung:

Das Element `<roleName>` enthält nur staatstragende Funktionen oder offizielle Titel;
Berufsbezeichnungen und sonstige Funktionen werden hier *nicht* angegeben.

## Friedrich II., König von Preußen

```
<persName ref="http://d-nb.info/gnd/118535749">
  <forename>Friedrich</forename>
  <genName>II.</genName>
  <roleName>König von Preußen</roleName>
</persName>
```

## Novalis

```
<persName ref="http://d-nb.info/gnd/118588893">
  <surname>Hardenberg</surname>
  <forename>Georg Philipp Friedrich</forename>
  <nameLink>von</nameLink>
  <addName>Novalis</addName>
</persName>
```

## Karl von Moor

```
<persName ref="nognd">
  <surname>Moor</surname>
  <forename>Karl</forename>
  <nameLink>von</nameLink>
</persName>
```


---

## Dokumentklassifikationen (//profileDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdProfileDesc.html](https://www.deutschestextarchiv.de/doku/basisformat/mdProfileDesc.html)

# Dokumentklassifikationen `(//profileDesc)`

Die *Profile Description* enthält Angaben zu den Sprachen, in welchen der Text hauptsächlich
verfasst ist (`<langUsage>/<language ident="[Code nach ISO 639-3]">`, [→ ISO 639-3](http://www-01.sil.org/iso639-3/codes.asp)), sowie Klassifizierungen der Texte
nach Textsorte, Thema und Herkunft des DTA-Volltextes (`<textClass>`).

Für die Klassifizierung nach Textsorten und Themen sind Mehrfachklassifizierungen möglich.
Die jeweils verwendeten Deskriptoren werden im Element `<classCode>` wiedergegeben.
Das Attribut `@scheme` in `<classCode>` enthält einen Verweis auf das
zugrundeliegende Klassifikationsschema, z.B. das
[Klassifikationsschema der DTA-Kernkorpus-Texte](http://www.deutschestextarchiv.de/doku/klassifikation).

Um die im DTA publizierten digitalisierten Volltextausgaben entsprechend ihrer Herkunft in Subkorpora zu
gruppieren, enthalten die Metadaten Angaben über den Kontext, in welchem der Volltext entstanden ist, sowie,
damit einhergehend, zur Erfassungsmethode (z.B. `china`, `ocr`, `mts`,
`aedit`, `gutenberg`, `wikisource`). Die entsprechende Angabe erfolgt jeweils in einem
`<classCode>`-Element, wiederum mit einem Verweis auf das zugrundeliegende Klassifikationsschema
(hier: das [Klassifikationsschema der DTA-Kernkorpus-Texte](http://www.deutschestextarchiv.de/doku/klassifikation))
im `@scheme`-Attribut.

```
<profileDesc>
  <langUsage>
    <language ident="[Code nach ISO 639-3, z.B. deu]">[Sprache, z.B. German]</language>
  </langUsage>
  <textClass>
    <classCode scheme="[URL DTA-Hauptklassifikation]">[Textsorte lt. DTA-Hauptklassifikation]</classCode>
    <classCode scheme="[URL DTA-Subklassifikation]">[Textsorte lt. DTA-Subklassifikation]</classCode>
    <classCode scheme="[URL DWDS-Hauptklassifikation01]">[Textsorte lt. DWDS-Hauptklassifikation 1]</classCode>
    <classCode scheme="[URL DWDS-Subklassifikation01]">[Textsorte lt. DWDS-Subklassifikation 1]</classCode>
    <classCode scheme="[URL DWDS-Hauptklassifikation02]">[Textsorte lt. DWDS-Hauptklassifikation 2]</classCode>
    <classCode scheme="[URL DWDS-Subklassifikation02]">[Textsorte lt. DWDS-Subklassifikation 2]</classCode>
    <classCode scheme="[URL Klassifikation Textherkunft]">[Herkunft des DTA-Volltextes]</classCode>
  </textClass>
</profileDesc>
```


---

## Die Grundstruktur des Publication Statements (//fileDesc/publicationStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdPubStmtAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdPubStmtAllg.html)

# Die Grundstruktur des *Publication Statements* `(//fileDesc/publicationStmt)`

Das *Publication Statement* (`<publicationStmt>`) der *File Description* enthält
publikationsspezifische Angaben zur jeweiligen DTA-Ausgabe:

* publizierende Institution (i.d.R. `"Berlin-Brandenburgische Akademie der Wissenschaften"`);
* herausgebendes Projekt (i.d.R. `"Deutsches Textarchiv"`);
* Erscheinungsdatum;
* Erscheinungsort;
* Lizenz, welche für die DTA-Ausgabe gilt (s. dazu Kap. [Lizenzangaben](mdLicense.html));
* Daten zur eindeutigen Identifikation des DTA-Volltextes: eindeutige ID-Nummer des DTA (`"DTAID"`), DTA-Verzeichnisname (`"DTADirName"`);
* Adressen der möglichen Zugänge zum Dokument, gruppiert in einem übergeordneten `<idno>`-Element:
  + Web-Präsentation (`"URLWeb"`, `"URN"`)
  + Download der XML/TEI-Fassung (`"URLXML"`)
  + Download der Text-Fassung (`"URLText"`)
  + Download der HTML-Fassung (`"URLHTML"`)
  + Download des durch die Ergebnisse der orthographischen Normalisierung mittels CAB angereicherten XML/TEI-Textes (`"URLCAB"`)
  + Download der TCF-Fassung (`"URLTCF"`)
  + Handle-PID des CMDI-Metadatensatzes (`"PIDCMDI"`)
  + DOI der digitalen Ausgabe (`"DOI"`)

Dabei steht das **`<publisher>`-Element** als Unterelement im `<publicationStmt>`
**grundsätzlich an erster Stelle**.

Achtung:

Bei den Adressen der möglichen Zugänge zum Dokument sollten Persistente Identifier (PIDs) verwendet werden,
um zu gewährleisten, dass die Quelle langfristig über die angegebene Adresse erreichbar ist.

```
<publicationStmt>
  <publisher xml:id="[ID, d.i. DTACorpusPublisher]"> <!-- grundsätzlich an erster Stelle -->
    <orgName role="hostingInstitution">[Publizierende Institution, d.i. Berlin-Brandenburgische Akademie der Wissenschaften]</orgName>
    <orgName role="project">[Herausgebendes Projekt, d.i. Deutsches Textarchiv]</orgName>
    <email>[E-Mail-Adresse der publizierenden Institution]</email>
    <address>
      <addrLine>[Adresse der publizierenden Institution]</addrLine>
    </address>
  </publisher>
  <pubPlace>[Publikationsort]</pubPlace>
  <date type="publication">[Publikationsdatum]</date>
  <availability xml:id="[ID]" corresp="[ID der zugehörigen Text-/Bildvorlage]"> <!-- ggf. mehrfach zu verwenden -->
    <licence target="[URL]">
      <p>[Hinweis zur Lizenz der Publikation]</p>
    </licence>
  </availability>
  <idno>
    <idno type="DTAID">[ID innerhalb des DTA-Korpus]</idno>
    <idno type="DTADirName">[Verzeichnisname innerhalb des DTA-Korpus]</idno>
    <idno type="URN">[URN der DTA-Onlinepublikation des Werkes]</idno>
    <idno type="URLWeb">[URL der DTA-Onlinepublikation des Werkes]</idno>
    <idno type="URLXML">[URL zum XML/TEI-Download der DTA-Publikation]</idno>
    <idno type="URLHTML">[URL zum HTML-Download der DTA-Publikation]</idno>
    <idno type="URLText">[URL zum Text-Download der DTA-Publikation]</idno>
    <idno type="URLCAB">[URL zum Download der CAB-Fassung der DTA-Publikation]</idno>
    <idno type="URLTCF">[URL zum TCF-Download der DTA-Publikation]</idno>
    <idno type="PIDCMDI">[Handle-PID zum CMDI-Metadatensatz der DTA-Publikation]</idno>
    <idno type="DOI">[DOI der digitalen Ausgabe]</idno>
  </idno>
</publicationStmt>
```


---

## Spezifika der DTA-Publikation (//fileDesc/publicationStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdPublicationStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdPublicationStmt.html)

# Spezifika der DTA-Publikation `(//fileDesc/publicationStmt)`

## Themen

* [Publication Statement Grundstruktur](mdPubStmtAllg.html)
* [Availability und Licence](mdLicense.html)


---

## Umgang mit externen Quellen für die DTA-Textgrundlage (//respStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdRespStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdRespStmt.html)

# Umgang mit externen Quellen für die DTA-Textgrundlage `(//respStmt)`

Externe Textressourcen, die im Rahmen von [DTAE](http://www.deutschestextarchiv.de/dtae) in die
DTA-Korpora aufgenommen werden, erhalten ein *Responsibility Statement*, in welchem deren Urheber und
ggf. Bearbeiter genannt und deren Beteiligung an der Textherstellung bzw. Texterschließung beschrieben werden.

Je nachdem, ob Einzelpersonen oder Institutionen/Organisationen/Projektgruppen für die Textressource verantwortlich
sind, werden diese im Element `<persName>` oder `<orgName>` wiedergegeben.

Das Element `<orgName>` kann ein `@ref`-Attribut zur Angabe einer Ressource erhalten
(mittels URL), das auf zusätzliche Angaben zu der genannten Organisation verweist, etwa auf den entsprechenden Datensatz
in der [Gemeinsamen Normdatei (GND)](http://www.dnb.de/DE/Standardisierung/GND/gnd_node.html).

Zur weiteren Unterstrukturierung des Elements `<persName>` s. [das entsprechende Kapitel](mdPersName.html).

Weitere Angaben zur Verantwortlichkeit werden im `<resp>`-Element des *Responsibility Statements*
vorgenommen. Dieses kann verschiedene Unterelemente erhalten:

* `<note type="remarkResponsibility">`: Angabe der Art der Verantwortlichkeit.
* `<note type="remarkRevisionDTA">`: Hinweis darauf, dass im Rahmen der Integration in das DTA sowie der
  DTA-Qualitätssicherung die externen Textressourcen weiter bearbeitet und aufbereitet werden (z. B. durch Konvertierung
  der Annotation in das DTA-Basisformat, durch das Beheben von Transkriptions- und Druckfehlern oder durch die weitere
  linguistische Aufbereitung); wird nur angegeben, falls das `<respStmt>` einen der DTA-Ausgabe zugrundeliegenden
  Volltext behandelt.
* `<date type="importDTA">`: Zeitpunkt, zu welchem die externe Ressource in ihrem gegebenen Bearbeitungsstand
  in das DTA integriert wurde. Das Datum sollte das folgende Format haben: yyyy-mm-dd"T"hh:mm:ss"Z", z.B.: 2014-04-08T13:09:00Z.
* `<ref target="[URL]"/>`: Verweis auf den Ursprungsort der integrierten Ressource (als URL). Dieses Element
  bleibt leer.

Wird in einem *Responsibility Statement* eine der DTA-Publikation zugrundeliegende Transkription des Werkes näher beschrieben,
so erhält das `<respStmt>`-Element eine eindeutige `@xml:id`. Über ein `@corresp`-Attribut wird es
mit einem `<availability>`-Element innerhalb des *Publication Statements* der *File Description*
verknüpft, welches die Lizenz der zugrundeliegenden Transkription angibt. Ist keine Lizenz bekannt, so wird dies im
`<licence>`-Element des `<availability>`-Elements entsprechend vermerkt
(siehe dazu Kap. [Lizenzangaben](mdLicense.html)). Eine Verknüpfung zu dem entsprechenden `<respStmt>` wird
dennoch hergestellt.

```
<respStmt> <!-- ggf. mit @xml:id="[ID]" und @corresp="[ID der zugehörigen Lizenzangabe]" -->
  <persName ref="[URL, z.B. Link zum GND-Datensatz]">[Urheber des zugrundeliegenden Volltextes (Person)]</persName> <!-- ggf. mehrfach zu verwenden; 
    zur weiteren Unterstrukturierung siehe oben -->
  <orgName ref="[URL, z.B. Link zum GND-Datensatz]">[Anbieter des zugrundeliegenden Volltextes (Organisation/Institution/Projektgruppe)]</orgName> 
  <!-- Angabe von @ref fakultativ-->
  <resp>
    <note type="remarkResponsibility">[Art der Verantwortlichkeit]</note>
    <note type="remarkRevisionDTA">[Hinweise auf mögliche Änderungen am Volltext im DTA]</note>
    <ref target="[URL einer externen Quelle]"/> <!-- ggf. mehrfach zu verwenden -->
    <date type="importDTA">[Datum der Integration der zugrundeliegenden Quelle in das DTA]</date>
  </resp>
</respStmt>
```

Wird das betreffende Werk am CLARIN-D-Zentrum Berlin-Brandenburgische Akademie der Wissenschaften archiviert
und somit im Rahmen des Verbundprojekts CLARIN-D langfristig zur Verfügung gestellt, so wird dies in einem
eigenen `<respStmt>`-Element dokumentiert, welches die folgenden Angaben enthält:

```
<respStmt>
  <orgName>CLARIN-D</orgName> 
  <resp>
    <note type="remarkResponsibility">Langfristige Bereitstellung der DTA-Ausgabe</note>
    <ref target="http://fedora.dwds.de"/>
  </resp>
</respStmt>
```


---

## Die Kurztitelangabe (//fileDesc/sourceDesc/bibl)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdBibl.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdBibl.html)

# Die Kurztitelangabe (//fileDesc/sourceDesc/bibl)

Das `<bibl>`-Element der `<sourceDesc>` enthält einen verkürzten bibliographischen Nachweis
zu der zugrundeliegenden Quelle.

Der jeweilige Publikationstyp wird im `@type`-Attribut des `<bibl>`-Elements angegeben. Folgende
`@type`-Werte sind dabei möglich:

|  |  |  |
| --- | --- | --- |
| `"M"` | monograph | Monographie |
| `"MM"` | volume within multi-volumed monograph | Teil einer mehrbändigen Monographie |
| `"DM"` | dependent part of monograph | unselbständiger Teil einer Monographie, z.B. Beitrag in einem Sammelband; Buchkapitel |
| `"DS"` | dependent publication of a volume, which is part of a series | unselbständige Schrift in einem Band, der Teil einer Reihe ist |
| `"MS"` | monographic title within series | selbständiger Band einer Reihe |
| `"MMS"` | volume of a multi-volumed publication, which itself is part of a series | Teil einer mehrbändigen Monographie, die ihrerseits Teil einer Reihe ist |
| `"JA"` | journal article | Artikel einer Zeitschrift/Zeitung |
| `"J"` | journal | Zeitschrift/Zeitung |

Zum Aufbau der bibliographischen Angabe innerhalb von `<bibl>`
s. Kap. [Transkription der Kurztitelaufnahme](mdKtAufnahme.html)


---

## Die vollständigen bibliographischen Angaben zur Quelle (//fileDesc/sourceDesc/biblFull)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdBiblFull.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdBiblFull.html)

# Die vollständigen bibliographischen Angaben zur Quelle `(//fileDesc/sourceDesc/biblFull)`

* [Full Bibliographic Citation Grundstruktur](mdSdBiblFullAllg.html)
* [Title Statement (Source)](mdSdTitleStmt.html)
* [Edition Statement (Source)](mdSdEditionStmt.html)
* [Extent (Source)](mdSdExtent.html)


---

## Grundstruktur der Full Bibliographic Citation (//fileDesc/sourceDesc/biblFull)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdBiblFullAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdBiblFullAllg.html)

# Grundstruktur der *Full Bibliographic Citation* `(//fileDesc/sourceDesc/biblFull)`

Die vollständigen bibliographischen Angaben (`<biblFull>`) innerhalb der
*Source Description* umfassen die Titelangaben zur Quelle (`<titleStmt>`)
mit den Angaben zu Titel (`<title>`), Autor (`<author>`) und
ggf. Herausgeber/Übersetzer (`<editor>`) des Werks. Darüber hinaus enthält das
`<biblFull>`-Element die Angabe zur Art der Ausgabe (`<editionStmt>`)
sowie Hinweise zum Seitenumfang des zugrundeliegenden Bandes (`<extent>`), zu den
Rahmenbedingungen der Textausgabe (`<publicationStmt>`) und, im Falle nicht-selbständiger
Textausgaben, zur übergeordneten Zeitschrift oder Reihe (`<seriesStmt>`).

```
<sourceDesc>
  <bibl>[Zitiertitel]</bibl>
  <biblFull>
    <titleStmt>
      <title>[Titel, Untertitel, Band]</title>
      <author>[Autor]</author> <!-- ggf. mehrfach zu verwenden -->
      <editor>[Herausgeber/Übersetzer]</editor> <!-- ggf. mehrfach zu verwenden -->
    </titleStmt>
    <editionStmt>
      <edition>[Art der zugrundeliegenden Textausgabe]</edition>
    </editionStmt>
    <extent>
      <measure type="pages">[Umfang des Bandes in Seiten]</measure>
    </extent>
    <publicationStmt>[Angaben zur Band-Ausgabe]</publicationStmt>
    <seriesStmt>[Angaben zur Reihe]</seriesStmt> <!-- gegebenenfalls -->
  </biblFull>
</sourceDesc>
```


---

## Die Angabe zur Art der zugrundeliegenden Textausgabe (//fileDesc/sourceDesc/biblFull/editionStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdEditionStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdEditionStmt.html)

# Die Angabe zur Art der zugrundeliegenden Textausgabe `(//fileDesc/sourceDesc/biblFull/editionStmt)`

Die Hinweise zur Nummer und Art der Auflage, welche der DTA-Ausgabe zugrunde liegt
(z.B. Erstausgabe, zweite verbesserte Neuauflage u.ä.) werden im
`<editionStmt>` innerhalb des `<biblFull>`-Elements der
*Source Description* angegeben. Das `<editionStmt>` erhält hierfür
das Unterelement `<edition>`.

Im `@n`-Attribut des `<edition>`-Elements steht die
normalisierte Auflagennummer, z.B. `"2"` für `"zweite, vermehrte Auflage"`.

```
<editionStmt>
  <edition n="[Auflagennummer]">[Art der zugrundeliegenden Textausgabe]</edition>
</editionStmt>
```

Das `<edition>`-Element bleibt leer, wenn die Vorlage keine expliziten
Hinweise zur Auflage enthält. Im `@n`-Attribut steht dann die rekonstruierte Auflagennummer.

```
<editionStmt>
      <edition n="[Auflagennummer]"/>
</editionStmt>
```

Das `@n`-Attribut des `<edition>`-Element ist obligatorisch. Kann die Auflagennummer
weder der Vorlage entnommen noch rekonstruiert werden, steht `"k.A."` (keine Angabe) im
`@n`-Attribut.


---

## Die Umfangsangabe zur zugrundeliegenden Quelle (//fileDesc/sourceDesc/biblFull/extent)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdExtent.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdExtent.html)

# Die Umfangsangabe zur zugrundeliegenden Quelle `(//fileDesc/sourceDesc/biblFull/extent)`

Die Umfangsangabe (`<extent>`) im `<biblFull>`-Element der
*Source Description* enthält die Angaben über den Seitenumfang der unmittelbaren Vorlage
des DTA-Volltextes.

```
<extent>
  <measure type="pages">[Umfang der Vorlage]</measure>
</extent>
```


---

## Angaben zum Aufbewahrungsort der Quelle (//fileDesc/sourceDesc/msDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdMsDesc.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdMsDesc.html)

# Angaben zum Aufbewahrungsort der Quelle `(//fileDesc/sourceDesc/msDesc)`

Die unmittelbaren Vorlagen für die Werke im DTA sind in der Regel Bilddateien (Faksimiles), die auf der Grundlage physischer
Exemplare der Werkausgaben erstellt wurden. Sowohl der Standort und die Beschaffenheit der physischen Exemplare als
auch der Fundort der zugehörigen Bilddateien werden in der *Manuscript Description* (`<msDesc>`)
der *Source Description* spezifiziert.

Dabei wird zunächst der Leitdruck (i.e. die Druckvorlage, der die Edition hauptsächlich folgt) näher beschrieben.
Gelegentlich, z.B. im Fall fehlender Seiten im Leitdruck, muss für die Transkription einzelner Seiten jedoch auf
ein weiteres Exemplar der Quellenausgabe zurückgegriffen werden. In diesem Fall wird das
`<msDesc>`-Element mehrfach verwendet, um sämtliche Textvorlagen zu beschreiben.

Das Element `<msIdentifier>` enthält eine eindeutige Spezifikation des der DTA-Ausgabe
zugrundeliegenden Exemplars. Der Fundort wird innerhalb von `<msIdentifier>`
durch die Angabe der besitzenden Bibliothek/Institution/Person (`<repository>`) sowie der
zugehörigen Identifikationsnummer(n) (`<idno>`) beschrieben.

Dabei steht für die Angabe der Identifikationsnummern innerhalb von `<msIdentifier>` genau ein
attributfreies `<idno>`-Element. Darin werden sämtliche Identifikationsnummern zu einem
Dokument in Form einzelner typisierter `<idno>`-Elemente subsummiert. Folgende Werte kann
das Attribut `@type` dabei annehmen:

* `"shelfmark"`: Signatur der physischen Textquelle;
* `"URLCatalogue"`:URL der Katalogaufnahme, in welchem das zugrundeliegende Exemplar verzeichnet ist;
* `"URLImages"`: URL der der Textdigitalisierung zugrundeliegenden Bilddateien;
* `"URN"`: URN der der Textdigitalisierung zugrundeliegenden Quelle.
* `"PPN"`: PPN (Pica-Produktionsnummer) der der Textdigitalisierung zugrundeliegenden Quelle.
* `"EPN"`: EPN (Exemplar-Produktionsnummer) der der Textdigitalisierung zugrundeliegenden Quelle.
* `"URLIIIF"`: URL des IIIF-Manifests der der Textdigitalisierung zugrundeliegenden Bilddateien.
* `"VD"`: VD-Nummer der der Textdigitalisierung zugrundeliegenden Quelle.

Achtung:

Als Adressen zur Identifikation der Quelle sollten Persistente Identifier (PIDs) verwendet werden,
um zu gewährleisten, dass die Quelle langfristig über die angegebene Adresse erreichbar ist.

Weiterhin enthält die *Manuscript Description* Angaben zu der im jeweiligen Band vorherrschenden
Schriftart (`<physDesc>/<typeDesc>`).

Über eine `@xml:id` und ein `@corresp`-Attribut ist jede *Manuscript Description*
eindeutig mit einem `<availability>`-Element innerhalb des *Publication Statements* der
*File Description* verknüpft, welches die Lizenz der Bilddateien angibt, die der DTA-Textausgabe zugrundeliegen
und im Rahmen der Web-Publikation mit dieser einhergehen. Ist keine Lizenz der Bilddateien bekannt, so wird dies
im `<licence>`-Element innerhalb des `<availability>`-Elements entsprechend vermerkt
(siehe dazu Kap. [Lizenzangaben](mdLicense.html)). Die Verknüpfung zu einer `<msDesc>` wird
dennoch hergestellt.

```
<msDesc xml:id="[ID]" corresp="[ID der zugehörigen Lizenz]"> <!-- ggf. mehrfach zu verwenden -->
  <msIdentifier>
    <repository>[besitzende Bibliothek/Institution/Person]</repository>
    <idno>
      <idno type="shelfmark">[Signatur]</idno>
      <idno type="URLCatalogue">[URL der Katalogaufnahme]</idno>
      <idno type="URLImages">[URL der Bilddateien]</idno>
      <idno type="URN">[URN der Bilddateien]</idno>
    </idno>
  </msIdentifier>
  <physDesc>
    <typeDesc>
      <p>[vorherrschende Schriftart, z.B. 'Fraktur']</p>
    </typeDesc> 
  </physDesc>
</msDesc>
```


---

## Editorischer Kommentar zur zugrundeliegenden Quelle (//fileDesc/sourceDesc/biblFull/notesStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdNotesStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdNotesStmt.html)

# Editorischer Kommentar zur zugrundeliegenden Quelle `(//fileDesc/sourceDesc/biblFull/notesStmt)`

Editorische Hinweise zur zugrundeliegenden Quelle werden innerhalb der
`<biblFull>`-Angabe der *Source Description* im Element
`<notesStmt>` wiedergegeben. Der jeweilige Wortlaut des
Kommentars steht im Notes Statement im Unterelement
`<note type="remarkSource">`.

```
<notesStmt>
  <note type="remarkSource">[Kommentar zur zugrundeliegenden Ausgabe]</note>
</notesStmt>
```

Die Hinweise im `<notesStmt>` umfassen z.B. die Begründung
der Auswahl der Ausgabe, falls diese nicht der Erstausgabe
des Werks entspricht. Weiterhin werden hier fehlerhafte bzw. unvollständige
Angaben des Titelblattes, welche in den Metadaten des TEI-Headers durch die
jeweils korrekte bzw. normalisierte Angabe ersetzt wurden, dokumentiert.


---

## Die Umstände der Textausgabe des zugrundeliegenden Bandes (//fileDesc/sourceDesc/biblFull/publicationStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdPublicationStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdPublicationStmt.html)

# Die Umstände der Textausgabe des zugrundeliegenden Bandes `(//fileDesc/sourceDesc/biblFull/publicationStmt)`

Die näheren Angaben zu den Umständen der Textausgabe, welche als Vorlage für den DTA-Volltext diente, werden im
*Publication Statement* (`<publicationStmt>`) innerhalb des `<biblFull>`-Elements
der *Source Description* wiedergegeben.

Dabei werden der Verlag bzw. die Druckerei, welche für die zugrundeliegende Textausgabe
verantwortlich zeichnen, im `<publisher>`-Element des
`<publicationStmt>`s angegeben. Das `<publisher>`-Element
bzw. die `<publisher>`-Elemente stehen immer an erster Stelle im
`<publicationStmt>`-Element, d.h. vor den Angaben zu Erscheinungsort
und Erscheinungsdatum der Quelle. Falls mehrere Angaben zu Verlag bzw. Druckerei notwendig
sind, so steht jede Angabe in einem separaten `<publisher>`-Element.

Der Erscheinungsort wird im `<pubPlace>`-Element des `<publicationStmt>`s
angegeben. Im Falle mehrerer Erscheinungsorte steht jeder einzelne Erscheinungsort ebenfalls in einem separaten
`<pubPlace>`-Element.

Die Datierung steht jeweils in einem Unterelement `<date>`. Über ein `@type`-Attribut
wird die Art der Datierung spezifiziert. Folgende Werte kann `@type` dabei annehmen:

| `@type`-Wert | Bedeutung |
| --- | --- |
| `publication` | Erscheinungsjahr der vorliegenden Quelle (obligatorisch) |
| `firstPublication` | Erscheinungsjahr der Erstausgabe, falls abweichend vom Erscheinungsjahr der Quelle |
| `creation` | Entstehungsjahr, falls abweichend vom Erscheinungsjahr der Quelle und vom Erscheinungsjahr der Erstausgabe |

```
<publicationStmt>
  <publisher> <!-- an erster Stelle; ggf. mehrfach zu verwenden -->
    <name>[Verlag/Druckerei]</name>
  </publisher>
  <pubPlace>[Erscheinungsort]</pubPlace> <!-- ggf. mehrfach zu verwenden -->  
  <date type="publication">[Erscheinungsjahr]</date>
  <date type="firstPublication">[Erscheinungsjahr der Erstausgabe]</date> <!-- gegebenenfalls -->
  <date type="creation">[Entstehungsjahr des Textes]</date> <!-- gegebenenfalls -->
</publicationStmt>
```


---

## Die Angaben zur übergeordneten Zeitschrift/Reihe der Quelle (//fileDesc/sourceDesc/biblFull/seriesStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdSeriesStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdSeriesStmt.html)

# Die Angaben zur übergeordneten Zeitschrift/Reihe der Quelle `(//fileDesc/sourceDesc/biblFull/seriesStmt)`

Ist die Vorlage als Band einer Reihe oder als Aufsatz innerhalb eines Bandes erschienen,
so werden die Angaben zur Reihe in einem *Series Statement* (`<seriesStmt>`)
innerhalb der *Source Description* festgehalten.

Dabei wird der Titel der übergeordneten Reihe/Zeitschrift in einem oder mehreren
`<title>`-Element(en) wiedergegeben. Das Attribut `@level` spezifiziert, welcher
Art die übergeordnete Publikation ist. Es kann die Werte `'s'` (series; Reihe) und `'j'`
(journal; Zeitschrift) annehmen. Das `@type`-Attribut gibt die Art des genannten Titels an. Es kann die Werte
`'main'` (Haupttitel) und `'sub'` (Untertitel) haben.

Der Ort der Publikation innerhalb der genannten Zeitschrift/Reihe wird in dem Element `<biblScope>` wiedergegeben.
Hierfür kann es mehrfach verwendet werden, wobei das `@unit`-Attribut die Art der jeweiligen Angabe spezifiziert.
Das `@unit`-Attribut kann dabei die folgenden Werte annehmen:

* `volume`: Jahrgang bei Zeitschriften/Band bei Reihen
* `issue`: Heft bei Zeitschriften
* `pages`: bei Zeitschriften Angabe, welche Seiten der Artikel umfasst

Das *Series Statement* ist somit unterschiedlich strukturiert, je nachdem, ob es sich bei dem
vorliegenden Werk um eine Monographie oder unselbständige Publikation innerhalb einer Reihe oder einen
Artikel innerhalb einer Zeitschrift handelt.

Im Falle einer Monographie innerhalb einer Reihe ist das `<seriesStmt>` wie folgt aufgebaut:

```
<seriesStmt>
  <title level="s" type="main">[Haupttitel der Reihe]</title>
  <title level="s" type="sub">[ggf. Untertitel der Reihe]</title>
  <biblScope unit="volume">[Bandbezeichnung für die Monographie innerhalb der Reihe]</biblScope>
</seriesStmt>
```

Im Falle einer *unselbständigen Publikation* innerhalb eines Sammelbandes in einer Reihe ist das
`<seriesStmt>` wie folgt aufgebaut:

```
<seriesStmt>
  <title level="s" type="main">[Haupttitel der Reihe]</title>
  <title level="s" type="sub">[ggf. Untertitel der Reihe]</title>
  <biblScope unit="volume">[Bandbezeichnung für den Sammelband innerhalb der Reihe]</biblScope>
  <biblScope unit="pages">[Seitenangabe]</biblScope>
</seriesStmt>
```

Im Falle einer *unselbständigen Publikation* innerhalb einer Zeitschrift
ist das `<seriesStmt>` wie folgt aufgebaut:

```
<seriesStmt>
  <title level="j" type="main">[Haupttitel der Zeitschrift]</title>
  <title level="j" type="sub">[ggf. Untertitel der Zeitschrift]</title>
  <biblScope unit="volume">[Jahrgang]</biblScope>
  <biblScope unit="issue">[Heft]</biblScope>
  <biblScope unit="pages">[Seitenangabe]</biblScope>
</seriesStmt>
```


---

## Die ausführlichen Titelangaben der Source Description (//fileDesc/sourceDesc/biblFull/titleStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSdTitleStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSdTitleStmt.html)

# Die ausführlichen Titelangaben der *Source Description* `(//fileDesc/sourceDesc/biblFull/titleStmt)`

Das `<title>`-Element im *Title Statement* der *Source Description*
enthält die Attribute `@level` und `@type`.
Mögliche Werte des `@level`-Attributs sind dabei:

* `m`: monographic title (Titel einer selbständigen Publikation/Monographie)
* `a`: analytic title (Titel einer nicht-selbständigen Publikation)

Mögliche Werte des `@type`-Attributs innerhalb von `<title>` sind:

* `main`: Haupttitel
* `sub`: Untertitel
* `volume`: Bandangabe/Bandtitel
* `part`: Titel des Teils bei mehrteiligen nicht-selbständigen Publikationen

Im Falle einer Bandangabe erhält das `<title>`-Element zudem ein `@n`-
Attribut, welches die Nummer des Bandes angibt:

```
<title level="m" type="volume" n="[Bandnummer]">[Bandtitel]</title>
```

Das `<author>`-Element gibt den Autor des Werkes an. Ein möglicher Herausgeber der zugrundeliegenden
Textquelle wird im `<editor>`-Element wiedergegeben. Handelt es sich bei der betreffenden Textausgabe
um eine Übersetzung, wird auf den Übersetzer mittels `<editor role="translator">`-Element verwiesen.
Zur tieferen Strukturierung des `<author>`- und `<editor>`-Elements siehe
Kap. [Unterstrukturierung der Elemente `<author>` und `<editor>`](mdAuthorEditor.html).


---

## Angaben zur zugrundeliegenden Quelle (//fileDesc/sourceDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSourceDesc.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSourceDesc.html)

# Angaben zur zugrundeliegenden Quelle `(//fileDesc/sourceDesc)`

## Themen

* [Source Description Grundstruktur](mdSourceDescAllg.html)
* [(Short) Bibliographic Citation](mdSdBibl.html)
* [Full Bibliographic Citation](mdSdBiblFull.html)
* [Publication Statement (Source)](mdSdPublicationStmt.html)
* [Series Statement (Source)](mdSdSeriesStmt.html)
* [Notes Statement (Source)](mdSdNotesStmt.html)
* [Manuscript Description (Source)](mdSdMsDesc.html)


---

## Grundstruktur der Source Description (//fileDesc/sourceDesc)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdSourceDescAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdSourceDescAllg.html)

# Grundstruktur der *Source Description* `(//fileDesc/sourceDesc)`

Hinweise zur Vorlage des DTA-Volltextes (zugrundeliegende Buchfassung und Bilddateien) werden
in der *Source Description* (`<sourceDesc>`) zusammengefasst.

Die Elemente `<bibl>` (*Bibliographic Citation*) und `<biblFull>`
(*Fully-structured Bibliographic Citation*) der *Source Description* enthalten die vollständigen
bibliographischen Angaben zu dem jeweils im DTA publizierten Band. Innerhalb von `<biblFull>`
werden außerdem der Umfang der Quelle (`<extent>`) sowie die Rahmenbedingungen der Ausgabe
(`<publicationStmt>`) angegeben. Für Angaben zum Aufbewahrungsort der Quelle steht das
Element `<msDesc>` (*Manuscript Description*) zur Verfügung.

```
<sourceDesc>
  <bibl type="[M | MM | DM | DS | JA | J | MMS | MS]">[Kurztitelangabe]</bibl>
  <biblFull>[bibliographische Angaben zur Quelle]</biblFull>
  <msDesc>[Angaben zum Aufbewahrungsort der Quelle]</msDesc>
</sourceDesc>
```


---

## Titelangaben

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdTitelangaben.html](https://www.deutschestextarchiv.de/doku/basisformat/mdTitelangaben.html)

# Titelangaben

Titelangaben werden grundsätzlich entsprechend den im Kapitel [Vorlagentreue bei der Aufnahme von
Metadaten](mdVorlagentreue.html) verzeichneten Richtlinien übernommen. Über diese
Regelungen hinaus werden die Titelangaben grundsätzlich ungeachtet
der Vorlage mit einem Großbuchstaben eingeleitet.

Titelangaben, die aufgrund ihrer Länge unübersichtlich werden, können verkürzt werden.
Auslassungen werden dabei mittels des Ausdrucks "`[...]`" markiert. Verkürzungen
des Titels dürfen jedoch dessen Sinn nicht entstellen.

## Titelangaben

*Siehe:* <http://www.deutschestextarchiv.de/pinter_pferdschatz_1688>

Die Angabe des Autors ist in der Regel nicht Teil des Titels. Würde jedoch durch den Wegfall
der Autorenangabe der Sinn des Titels entstellt, so wird diese mit übernommen. Gleiches gilt
für die Angabe des Bandes als Teil des Haupttitels.

## Umgang mit Autornennung im Titel

*Siehe:* <http://www.deutschestextarchiv.de/hoffmannswaldau_gedichte02_1697>

Angaben zu Anhängen und Beigaben (z.B. "Mit zwei Abbildungen im Text und XXI Tafeln.") gelten
nicht als Teil des Titels und werden somit nicht in die Titelaufnahme übernommen.


---

## Die Titelangaben innerhalb der File Description (//fileDesc/titleStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdTitleStmt.html](https://www.deutschestextarchiv.de/doku/basisformat/mdTitleStmt.html)

# Die Titelangaben innerhalb der *File Description* `(//fileDesc/titleStmt)`

## Themen

* [Title Statement Grundstruktur](mdTitleStmtAllg.html)
* [Author und Editor](mdAuthorEditor.html)
* [Personal Name](mdPersName.html)
* [Responsibility Statement](mdRespStmt.html)


---

## Die Grundstruktur des Title Statements (//fileDesc/titleStmt)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdTitleStmtAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/mdTitleStmtAllg.html)

# Die Grundstruktur des *Title Statements* `(//fileDesc/titleStmt)`

Das *Title Statement* (`<titleStmt>`) der *File Description* dient zur Angabe von Titel(n)
(im Element `<title>`) und Autor(en) (im Element `<author>`) des jeweiligen Werks
sowie der Herausgeber der DTA-Volltextausgabe (im Element `<editor>`). Darüber hinaus werden hier
mögliche weitere Verantwortlichkeiten für einzelne Instanzen des Textes im Digitalisierungprozess geklärt (im
Element `<respStmt>`).

```
<titleStmt>
  <title type="main">[Haupttitel]</title>
  <title type="sub">[Untertitel]</title> <!-- ggf. mehrfach zu verwenden -->
  <title type="volume" n="[DTA-Bandnummer]">[Bandbezeichnung]</title> <!-- falls vorhanden -->
  <title type="part" n="[Nummer des Teils einer mehrteiligen unselbständigen Publikation]">
    [Titel des Teils einer mehrteiligen unselbständigen Publikation]
  </title> <!-- falls vorhanden -->
  <author>[Autor]</author> <!-- ggf. mehrfach zu verwenden -->
  <editor corresp="#[XML-ID des Publication Statements]">
    [Herausgeber der vorliegenden Textausgabe]
  </editor> <!-- ggf. mehrfach zu verwenden -->
  <respStmt>[Verantwortlichkeit bei externen Beiträgern]</respStmt>
</titleStmt>
```

VORSICHT:

Im `<titleStmt>` der *File Description* werden der (die) Autor(en) des Werks
sowie die Herausgeber der vorliegenden DTA-Textausgabe angegeben. Mögliche Herausgeber/Übersetzer der
zugrundeliegenden Quelle werden erst in der *Source Description* aufgeführt, auch wenn das Werk
keinem Autor zugeordnet werden kann. Siehe dazu Kap. [Angaben zur zugrundeliegenden Quelle](mdSourceDesc.html).

Siehe unten zur [Unterstrukturierung der Elemente `<author>` und `<editor>`](mdAuthorEditor.html)
sowie zur [Unterstrukturierung des Elements `<respStmt>`](mdRespStmt.html).


---

## Transkriptionsrichtlinien für die Aufnahme von Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdTranskription.html](https://www.deutschestextarchiv.de/doku/basisformat/mdTranskription.html)

# Transkriptionsrichtlinien für die Aufnahme von Metadaten

Um die Einheitlichkeit der erfassten Metadaten zu gewährleisten, werden im
Folgenden ausführliche Richtlinien für die Erfassung (Transkription) von
Metadaten entsprechend dem DTA-Basisformat bereitgestellt.

## Themen

* [Vorlagentreue](mdVorlagentreue.html)
* [Normalisierungen](mdNormalisierungen.html)
* [Besonderheiten der Metadatenerfassung](mdBesonderheitenErfassung.html)


---

## Umgang mit typographischen Hervorhebungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdTypographHervorhebungen.html](https://www.deutschestextarchiv.de/doku/basisformat/mdTypographHervorhebungen.html)

# Umgang mit typographischen Hervorhebungen

Typographische Hervorhebungen der Vorlage, wie etwa gedruckte Initialen,
Fett- oder Kursivdruck werden nicht in die Metadaten übernommen.

Der Zeilenfall wird stillschweigend aufgehoben, d.h. es erfolgt keinerlei
Markierung des ursprünglichen Zeilenfalls innerhalb des Titels. Trennungen
am Zeilenende werden aufgehoben.

Im Falle von Majuskelschrift wird wie folgt normalisiert:

* Deutschsprachige Titel: Die Groß-/Kleinschreibung folgt den heutigen Regeln.
  Die Majuskel "J" am Beginn eines Wortes wird als "J" wiedergegeben.
* Titel in lateinischer Sprache: Grundsätzlich erfolgt Kleinschreibung;
  Großschreibung im Anlaut erfolgt allein am Beginn des Titels und bei Eigennamen.


---

## Überblick über die DTA-Spezifikation für den TEI-Header

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdUeberblick.html](https://www.deutschestextarchiv.de/doku/basisformat/mdUeberblick.html)

# Überblick über die DTA-Spezifikation für den TEI-Header

Im Folgenden wird die DTA-Spezifikation des TEI-Headers in ihrer
Gesamtheit beispielhaft präsentiert.

```
<teiHeader>
  <fileDesc>
    <titleStmt>
      <title type="main">[Haupttitel]</title> 
      <title type="sub">[Untertitel]</title> 
      <title type="volume" n="[DTA-Bandnummer]">[Bandnummer und ggf. -titel]</title>
      <title type="part" n="[Nummer des Teils einer mehrteiligen unselbständigen Publikation]">
        [Titel des Teils einer mehrteiligen unselbständigen Publikation]</title>
      <author><!-- Autor des Werks -->
        <persName ref="[URL, z.B. Link zum GND-Datensatz]">
          <surname>[Familienname des Autors]</surname>
          <forename>[Vorname des Autors]</forename>
          <nameLink>[Namenszusatz, z.B. Adelsprädikat]</nameLink>
          <genName>[Generation]</genName>
          <addName>[ggf. Pseudonym oder sonstiger zusätzlicher Name]</addName>
          <roleName>[Funktion, welche die Person ausübt(e)]</roleName>
        </persName>
      </author>
      <editor corresp="#[XML-ID von publicationStmt]"><!-- Herausgeber der vorliegenden Textausgabe -->
        <persName ref="[URL, z.B. Link zum GND-Datensatz]">
          <surname>[Familienname des Herausgebers]</surname>
          <forename>[Vorname des Herausgebers]</forename>
          <!-- [siehe oben für weitere mögliche Unterelemente] -->
        </persName>
      </editor>
      <respStmt xml:id="[ID; gegebenenfalls]" corresp="[ID der zugehörigen Lizenzangabe; gegebenenfalls]">
        <persName ref="[URL, z.B. Link zum GND-Datensatz]"> <!-- Urheber/Bearbeiter des zugrundeliegenden Volltextes (Person); ggf. mehrfach zu verwenden -->
          <surname>[Familienname des Herausgebers]</surname>
          <forename>[Vorname des Herausgebers]</forename>
          <!-- [siehe oben für weitere mögliche Unterelemente] -->
        </persName> 
        <orgName ref="[URL, z.B. Link zum GND-Datensatz]">[Anbieter des zugrundeliegenden Volltextes (Organisation/Institution/Projektgruppe)]</orgName> <!-- Angabe von @ref fakultativ-->
        <resp>
          <note type="remarkResponsibility">[Art der Verantwortlichkeit]</note>
          <note type="remarkRevisionDTA">[Hinweise auf mögliche Änderungen am Volltext im DTA]</note>
          <ref target="[Verweis auf eine externe Quelle]"/> <!-- ggf. mehrfach zu verwenden -->
          <date type="importDTA">[Datum der Integration der zugrundeliegenden Quelle in das DTA]</date>
        </resp>
      </respStmt>
    </titleStmt>
    <editionStmt>
      <edition>[Art der vorliegenden Textausgabe]</edition>
    </editionStmt> 
    <extent> 
      <measure type="images">[Umfang in Bilddateien]</measure> 
      <measure type="tokens">[Umfang in Tokens]</measure> 
      <measure type="types">[Umfang in Types]</measure> 
      <measure type="characters">[Umfang in Zeichen]</measure> 
    </extent>
    <publicationStmt>
      <publisher xml:id="[ID, d.i. DTACorpusPublisher]"> <!-- an erster Stelle im Publication Statement -->
        <orgName role="hostingInstitution">[Publizierende Institution, d.i. Berlin-Brandenburgische Akademie der Wissenschaften]</orgName>
        <orgName role="project">[Herausgebendes Projekt, d.i. Deutsches Textarchiv]</orgName>
        <email>[E-Mail-Adresse der publizierenden Institution]</email>
        <address>
          <addrLine>[Adresse der publizierenden Institution]</addrLine>
        </address>
      </publisher>
      <pubPlace>[Publikationsort]</pubPlace>
      <date type="publication">[Publikationsdatum]</date>
      <availability xml:id="[ID]" corresp="[ID der zugehörigen Text-/Bildvorlage]"> <!-- ggf. mehrfach zu verwenden -->
        <licence target="[URL]">
          <p>[Hinweis zur Lizenz der Publikation]</p>
        </licence>
      </availability>
      <idno>
        <idno type="DTAID">[ID innerhalb des DTA-Korpus]</idno>
        <idno type="DTADirName">[Verzeichnisname innerhalb des DTA-Korpus]</idno>
        <idno type="URN">[URN der DTA-Onlinepublikation des Werkes]</idno>
        <idno type="URLWeb">[URL der DTA-Onlinepublikation des Werkes]</idno>
        <idno type="URLXML">[URL zum XML/TEI-Download der DTA-Publikation]</idno>
        <idno type="URLHTML">[URL zum HTML-Download der DTA-Publikation]</idno>
        <idno type="URLText">[URL zum Text-Download der DTA-Publikation]</idno>
        <idno type="URLCAB">[URL zum Download der CAB-Fassung der DTA-Publikation]</idno>
        <idno type="URLTCF">[URL zum TCF-Download der DTA-Publikation]</idno>
        <idno type="PIDCMDI">[Handle-PID zum CMDI-Metadatensatz der DTA-Publikation]</idno>
      </idno>
    </publicationStmt>
    <notesStmt>
      <note type="remarkDocument">[Zusatzinformationen zum Dokument]</note>
    </notesStmt>
    <sourceDesc>
      <bibl type="[M | MM | DM | DS | JA | J | MMS | MS]">[Zitiertitel]</bibl>
      <biblFull>
        <titleStmt>
          <title level="m" type="main">[Haupttitel einer Monographie]</title>
          <title level="m" type="sub">[Untertitel einer Monographie]</title>
          <title level="m" type="volume" n="[DTA-Bandnummer]">[Bandangabe einer Monographie]</title>
          <!-- auch level="a" ggf. mit type="part" für nichtselbständige Publikationen möglich -->
          <author>
            <persName ref="[ggf. Link zu externer Ressource, z.B. GND-Datensatz]">
              <surname>[Familienname des Autors]</surname>
              <forename>[Vorname des Autors]</forename>
              <!-- [siehe oben für weitere mögliche Unterelemente] -->
            </persName>
          </author>
          <editor> <!-- Herausgeber der zugrundeliegenden Textausgabe; bei Übersetzer: @role="translator" -->
            <persName ref="[ggf. Link zu externer Ressource, z.B. GND-Datensatz]">
              <surname>[Familienname des Herausgebers]</surname>
              <forename>[Vorname des Herausgebers]</forename>
              <!-- [siehe oben für weitere mögliche Unterelemente] -->
            </persName>
          </editor>
        </titleStmt>
        <editionStmt>
            <edition n="[normierte Ausgabennummer]">[Hinweis zur Ausgabe entsprechend der Vorlage]</edition>
        </editionStmt>
        <extent>
          <measure type="pages">[Umfang der Quelle in Seiten]</measure>
        </extent>
        <publicationStmt>
          <publisher> <!-- an erster Stelle im Publication Statement; ggf. mehrfach zu verwenden --> 
            <name>[Verlag/Druckerei]</name>
          </publisher>
          <pubPlace>[Druckort]</pubPlace>
          <date type="publication">[Erscheinungsjahr]</date>
          <date type="firstPublication">[Erscheinungsjahr der Erstausgabe]</date> <!-- falls bekannt und abweichend vom Erscheinungsjahr -->
          <date type="creation">[Entstehungsjahr des Textes]</date> <!-- falls bekannt und abweichend vom Erscheinungsjahr -->
        </publicationStmt>
        <notesStmt>
          <note type="remarkSource">[ggf. Kommentar zur zugrundeliegenden Ausgabe]</note>
        </notesStmt>
        <seriesStmt> <!-- ggf. Angabe zur übergeordneten Publikation -->
          <title level="j" type="main">[Titel der Zeitschrift]</title>
          <!-- auch level="s" für übergeordnete Reihe (series) und type="sub" für Untertitel möglich -->
          <biblScope unit="volume">[Band einer Reihe/Jahrgang einer Zeitschrift]</biblScope>
          <biblScope unit="issue">[Heft bei Zeitschriften]</biblScope>
          <biblScope unit="pages">[Seitenangabe]</biblScope>
        </seriesStmt>
      </biblFull>
      <msDesc xml:id="[ID]" corresp="[ID des zugehörigen availability-Elements]"> <!-- ggf. mehrfach zu verwenden -->
        <msIdentifier>
          <repository>[besitzende Bibliothek/Institution/Person]</repository>
          <idno>
            <idno type="shelfmark">[Signatur]</idno>
            <idno type="URLCatalogue">[URL der Katalogaufnahme]</idno>
            <idno type="URLImages">[URL der Bilddateien]</idno>
            <idno type="URN">[URN der Bilddateien]</idno>
          </idno>
        </msIdentifier>
        <physDesc>
          <typeDesc>
            <p>[vorherrschende Schriftart, z.B. 'Fraktur']</p>
          </typeDesc> 
        </physDesc>
      </msDesc>
    </sourceDesc>
  </fileDesc>
  <encodingDesc> 
    <editorialDecl>
      <p>[Angaben zu den Transkriptions- und Annotationsrichtlinien]</p>
      <p>[weitere Angaben zu den Transkriptions- und Annotationsrichtlinien]</p>
    </editorialDecl>
  </encodingDesc> 
  <profileDesc>
    <langUsage>
      <language ident="[Code nach ISO 639-3]">[Sprache]</language> 
    </langUsage>
    <textClass>
      <classCode scheme="[URL DTA-Hauptklassifikation]">[Textsorte lt. DTA-Hauptklassifikation]</classCode>
      <classCode scheme="[URL DTA-Subklassifikation]">[Textsorte lt. DTA-Subklassifikation]</classCode>
      <classCode scheme="[URL DWDS-Hauptklassifikation01]">[Textsorte lt. DWDS-Hauptklassifikation 1]</classCode>
      <classCode scheme="[URL DWDS-Subklassifikation01]">[Textsorte lt. DWDS-Subklassifikation 1]</classCode>
      <classCode scheme="[URL DWDS-Hauptklassifikation02]">[Textsorte lt. DWDS-Hauptklassifikation 2]</classCode>
      <classCode scheme="[URL DWDS-Subklassifikation02]">[Textsorte lt. DWDS-Subklassifikation 2]</classCode>
      <classCode scheme="[URL Klassifikation Textherkunft]">[Herkunft des DTA-Volltextes]</classCode>
    </textClass>
  </profileDesc>
</teiHeader>
```


---

## Umgang mit unvollständigen Angaben

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdUnvollstAngaben.html](https://www.deutschestextarchiv.de/doku/basisformat/mdUnvollstAngaben.html)

# Umgang mit unvollständigen Angaben

## Rekonstruierbare Angaben

Notwendige Angaben, die auf den Titelblättern der Vorlage fehlen, z.B. der
Erscheinungsort, das Erscheinungsjahr, die Verlagsangabe, der Autor, werden
möglichst rekonstruiert.

Die rekonstruierten Angaben erscheinen im Kurztitel in eckigen Klammern.

## Rekonstruierte Angaben im Kurztitel

```
[Calvi, François de]: Beutelschneider, oder newe warhaffte
        vnd eigentliche Beschreibung der Diebs Historien. [Bd. 1]. Frankfurt (Main), 1627.
```

<http://www.deutschestextarchiv.de/calvi_beutelschneider01_1627>

In den sonstigen dafür vorgesehenen Feldern werden diese Angaben ohne weitere
Hinweise auf deren Rekonstruktion eingetragen.

## Rekonstruierte Angaben außerhalb des Kurztitels

*Siehe:*
<http://www.deutschestextarchiv.de/calvi_beutelschneider01_1627>

Eine Ausnahme bildet die Verlagsangabe, die nicht im Kurztitel erscheint. Ist diese
rekonstruiert, so wird dies im `<notesStmt>` der `<sourceDesc>`
entsprechend vermerkt.

## Rekonstruierte Angabe des Verlags

*Siehe:*
<http://www.deutschestextarchiv.de/api/tei_header/hellwig_haussverwalter_1712>

## Nicht-rekonstruierbare Angaben

Lässt sich eine Angabe nicht rekonstruieren, so wird gemäß der folgenden Tabelle darauf hingewiesen.

| Rekonstruierte Angabe | Schreibweise | Hinweise |
| --- | --- | --- |
| Autor | `N. N.` | (Nomen nescio.) Ausnahmen sind Zeitungen, Lexika oder von offizieller Seite herausgegebene Werke, die auf ein nicht näher spezifizierbares Autorenkollektiv zurückgehen (z. B. Gesetzeswerke, Urkunden, Edikte); hier bleibt die Autorangabe leer. |
| Erscheinungsort | `s. l.` | (sine loco) Ausnahme: Manuskripte; hier wird auf eine Ortsangabe verzichtet. |
| Verlag | `s. e.` | (sine editore) Ausnahme: Manuskripte; hier wird auf eine Verlagsangabe verzichtet. |

Im Kurztitel werden diese Angaben durch eckige Klammern umschlossen, um anzuzeigen, dass es sich
dabei um editorische Ergänzungen handelt. In den vollständigen Titelangaben steht die jeweilige Angabe ohne
Umklammerung.

## Hinweise auf Unbekanntes im Kurztitel

```
Naumann, Bernhard: Der aufrichtige Leipziger Roßarzt. [s. l.], 1780.
```

```
[N. N.]: Ein Koch- Und Artzney-Buch. 2. Aufl. Grätz, 1688.
```


---

## Umgang mit verfälschten/verschleierten Angaben

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdVerfaelschteAngaben.html](https://www.deutschestextarchiv.de/doku/basisformat/mdVerfaelschteAngaben.html)

# Umgang mit verfälschten/verschleierten Angaben

In der Quelle verfälschte Angaben zur Publikation (z.B. das Werk erschien unter
einem Pseudonym oder Erscheinungsort/Verlag etc. sind fiktiv) werden in ihrer
ursprünglichen, in der Quelle erscheinenden Form im Kurztitel wiedergegeben.
Dabei steht im Falle eines Pseudonyms der vollständige Name so weit bekannt
ohne spezifische Unterteilung (z. B. richtig: `Vorname Adelstitel Nachname`;
falsch: `Nachname, Vorname Adelstitel`). Die korrekte Angabe wird recherchiert
und im Anschluss an die ursprüngliche Form in eckigen Klammern, eingeleitet durch
`i.e.` im Kurztitel wiedergegeben.

## Rekonstruktion des Autornamens im Kurztitel

German Schleifheim von Sulsfort [i. e. Grimmelshausen, Hans Jakob Christoffel von]:
Der Abentheurliche Simplicissimus Teutsch. Monpelgart [i. e. Nürnberg], 1669.

In den ausführlichen Titelangaben steht im Falle eines Pseudonyms zunächst der bürgerliche
Name, aufgeteilt in `<surname>` (Nachname) und `<forename>`
(Vorname) ohne weitere Hinweise auf deren Rekonstruktion. Sodann folgt das Pseudonym im Element
`<addName>`, wobei auch hier der vollständige Name so weit bekannt ohne
spezifische Unterteilung (z. B. richtig: `Vorname Adelstitel Nachname`;
falsch: `Nachname, Vorname Adelstitel`) angegeben wird.

Achtung:

Das Pseudonym wird nur dann angegeben, wenn ein Werk unter diesem Pseudonym
erschienen ist. Ist ein Werk unter dem bürgerlichen Namen eines Autors erschienen, so wird
allein der bürgerliche Name angegeben, auch wenn es ein Pseudonym für den betreffenden Autor
gibt. Dass ein Werk unter einem Pseudonym erschienen ist, lässt sich somit entsprechend der
vorliegenden Richtlinie daran erkennen, dass ein `<addName>`-Element im
Metadatensatz vorhanden und befüllt ist.

Im Falle eines fiktiven Erscheinungsorts oder Verlags steht in den ausführlichen Titelangaben
die rekonstruierte Angabe zunächst ohne weitere Hinweise auf deren Rekonstruktion. Beim
Erscheinungsort wird im Kurztitel verdeutlicht, dass es sich um eine rekonstruierte Angabe handelt (s. oben).
Bei der Verlagsangabe, die nicht im Kurztitel erscheint, wird im `<notesStmt>`
der `<sourceDesc>` ein natürlichsprachlicher Hinweis auf die Rekonstruktion gegeben.

## Korrektur verfälschter Verlags-/Orts- und Autorangaben in den Metadaten:

*Siehe:* <http://www.deutschestextarchiv.de/api/tei_header/grimmelshausen_simplicissimus_1669>


---

## Verlag

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdVerlag.html](https://www.deutschestextarchiv.de/doku/basisformat/mdVerlag.html)

# Verlag

Der Name des Verlags bzw. der Druckerei eines Werks wird grundsätzlich vorlagengetreu wiedergegeben.

*Ausnahmen:*

* Namenszusätze (z.B. "& Co.", "und Söhne") werden nicht wiedergegeben.
* Für Werke, die im Selbstverlag erschienen sind, steht ungeachtet der Vorlage grundsätzlich
  der Terminus "`Selbstverlag`".

## Angabe des Selbstverlags

*Siehe:* <http://www.deutschestextarchiv.de/euler_algebra02_1770>


---

## Vorlagentreue bei der Aufnahme von Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mdVorlagentreue.html](https://www.deutschestextarchiv.de/doku/basisformat/mdVorlagentreue.html)

# Vorlagentreue bei der Aufnahme von Metadaten

Den Metadatenaufnahmen nach DTA-Basisformat werden grundsätzlich die Titeldaten,
welche sich auf den Titelseiten des jeweiligen Werks befinden, zugrunde gelegt.
Die originale Schreibweise wird dabei grundsätzlich beibehalten, d.h. historische
Schreibungen werden nicht modernisiert, die Groß-/Kleinschreibung der Vorlage wird
beibehalten.

Ausgenommen von dieser Regel sind Personen- und Ortsnamen (s. Kap.
[Autor/Herausgeber/Übersetzer](mdAutorHrsgUebers.html) und Kap.
[Erscheinungsort](mdErscheinungsort.html)).

Von dieser Regel kann darüber hinaus abgewichen werden, wenn die
auf den Titelseiten verzeichneten Titeldaten:

* typographisch hervorgehoben wurden (z.B. durch Majuskelschrift);
* mit heutzutage ungebräuchlichen Sonderzeichen versehen wurden (z.B. aͤ,
  oͤ, uͤ);
* unvollständig sind (z.B. Angaben zum Erscheinungsort bzw. -jahr fehlen);
* verkürzt wurden (z.B. durch Verwendung von Nasalstrichen);
* bewusst gefälscht oder verschleiert wurden (z.B. durch Verwendung von
  Pseudonymen oder fiktiven Orten);
* fehlerhaft sind (z.B. im Falle eindeutiger Druckfehler).

In diesen Fällen sind zugunsten der Auffindbarkeit der Werke Normalisierungen bzw.
Korrekturen an den Titeldaten gegenüber der Vorlage möglich.


---

## DTA-Basisformat – Erschließung der Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/metadaten.html](https://www.deutschestextarchiv.de/doku/basisformat/metadaten.html)

# DTA-Basisformat – Erschließung der Metadaten

Erfassung (Transkription) und Auszeichnung von Metadaten

Das DTA-Basisformat sieht ausführliche Metadaten für alle Dokumente vor.
Diese Metadaten umfassen eine Beschreibung der digitalen Ausgabe inklusive ihrer
verantwortlichen Personen und Institutionen, sowie ausführliche Hiinweise auf
die zugrundeliegende physische Quelle.

Um die Einheitlichkeit der erfassten Metadaten zu gewährleisten, werden neben den
Richtlinien für die Auszeichnung der Metadaten im Folgenden auch Transkriptionsrichtlinien
für Metadaten bereitgestellt.


---

## Hinzufügungen und Tilgungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msAddDel.html](https://www.deutschestextarchiv.de/doku/basisformat/msAddDel.html)

# Hinzufügungen und Tilgungen

Sekundäre Änderungen des Autors oder eines späteren Bearbeiters am Manuskript können
in Form von Tilgungen oder Hinzufügungen auftreten. Hierfür werden die Elemente
`<add>` (Hinzufügung) und `<del>` (Tilgung) verwendet.

```
<add>[Hinzufügung]</add>
```

```
<del>[Tilgung]</del>
```

Im Fall einer Hinzufügung kann das `<add>`-Element durch ein
`@place`-Attribut ergänzt werden, in dem der Ort der Hinzufügung angegeben
wird. Folgende Werte von `@place` sind dabei möglich:

| Element | `@place`-Wert | Bedeutung |
| --- | --- | --- |
| `<add>` | `superlinear` | über der Zeile eingetragen |
| `sublinear` | unter der Zeile eingetragen |
| `intralinear` | innerhalb der Zeile eingetragen |
| `across` | über den ursprünglichen Text geschrieben |
| `left` | am linken Rand eingetragen |
| `right` | am rechten Rand eingetragen |

Im Fall einer Tilgung wird die Art der Tilgung mit dem `@rendition`-Attribut
des `<del>`-Elements wiedergegeben. Dabei sind folgende Werte für `@rendition`
möglich:

| Element | `@rendition`-Wert | Bedeutung |
| --- | --- | --- |
| `<del>` | `#ow` | Tilgung durch Überschreibung des ursprünglichen Textes |
| `#s` | Tilgung durch Streichung |
| `#erased` | Tilgung durch Radieren, Auskratzen o. ä. |


---

## Sekundäre Textänderungen des Autors und späterer Bearbeiter

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msAenderungen.html](https://www.deutschestextarchiv.de/doku/basisformat/msAenderungen.html)

# Sekundäre Textänderungen des Autors und späterer Bearbeiter

## Themen

* [Hinzufügungen und Tilgungen](msAddDel.html)
* [Substitutionen](msSubst.html)


---

## Allgemeines zur Kodierung von Manuskripten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/msAllg.html)

# Allgemeines zur Kodierung von Manuskripten

## Geltungsbereich der vorliegenden Richtlinien

Die Auszeichnung von Manuskripten erfolgt grundsätzlich entsprechend dem
DTA-Basisformat (DTABf). Die vorliegende Spezifikation bezieht
sich lediglich auf Besonderheiten von Manuskripten, die im
Kern-DTABf nicht berücksichtigt sind.

Für die Validierung von Manuskripten steht ein eigenes RNG-Schema zur Verfügung:
[DTABf-Schema für Manuskripte ⇗](http://www.deutschestextarchiv.de/basisformat_ms.rng).
Für Informationen zur Nutzung des Schemas vgl. Kapitel [Verfügbarkeit des Schemas](benutzungDTABfSchema.html).

## Terminologische Konventionen der vorliegenden Richtlinien

**Autor:** Der historische Autor der Handschrift.

**Bearbeiter:** Ein späterer Bearbeiter der Handschrift, dessen
Anmerkungen/Korrekturen/Hinzufügungen die Handschrift trägt.

**Editor:** Der Herausgeber der in Bearbeitung befindlichen
digitalen Ausgabe.


---

## Anmerkungen des Autors oder späterer Bearbeiter

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msAnmerkungen.html](https://www.deutschestextarchiv.de/doku/basisformat/msAnmerkungen.html)

# Anmerkungen des Autors oder späterer Bearbeiter

Anmerkungen des Autors oder späterer Bearbeiter zum Text werden im
`<note>`-Element wiedergeben. Der Ort, an dem die Anmerkung
eingetragen ist, wird im @place-Attribut spezifiziert. Das
@place-Attribut kann dabei die folgenden Werte annehmen:

| @place-Wert | Bedeutung |
| --- | --- |
| mTop | Anmerkung am oberen Rand |
| mBottom | Anmerkung am unteren Rand |
| inline | Anmerkung innerhalb der Zeile |

```
<note place="mTop">[Anmerkung am oberen Rand]</note>
```


---

## Inventar des Editors der digitalen Ausgabe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msEditorBearbeitung.html](https://www.deutschestextarchiv.de/doku/basisformat/msEditorBearbeitung.html)

# Inventar des Editors der digitalen Ausgabe

## Themen

* [Verantwortlichkeiten](msEditorResp.html)
* [Unsichere Lesarten](msEditorCert.html)


---

## Unsichere Lesarten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msEditorCert.html](https://www.deutschestextarchiv.de/doku/basisformat/msEditorCert.html)

# Unsichere Lesarten

Ist die Leserlichkeit der Quelle eingeschränkt, sodass der Text rekonstruiert werden
muss bzw. die Lesung des Editors nicht gesichert ist, kann dies durch die Elemente
`<unclear>` und `<supplied>` wiedergegeben werden.

Dabei wird `<unclear>` verwendet, wenn in der
Quelle vorhandenes Material nur undeutlich lesbar ist. Der Grund für
die Verwendung des `<unclear>`-Elements wird
mit dem `@reason`-Attribut, der Grad der Sicherheit
der Lesung kann im `@cert`-Attribut wiedergegeben
werden. Folgende Werte sind dabei möglich:

| Element | Attribut | Wert | Bedeutung |
| --- | --- | --- | --- |
| `<unclear>` | `@reason` | `illegible` | unleserlich |
| `covered` | durch Überschreibung/Überzeichnung schwer leserlich |
| `@cert` | `high` | hohe Sicherheit der Lesart |
| `low` | geringe Sicherheit der Lesart |

Die Verwendung des Attributs `@reason` in
`<unclear>` ist dabei obligatorisch, die
Verwendung von `@cert` ist fakultativ.

```
<unclear reason="covered" cert="low">[unsichere Lesung]</unclear>
```

Wenn in der Quelle wahrscheinlich oder möglicherweise vorhandenes
Material rekonstruiert wird, so ist dies mit dem Element
`<supplied>` wiederzugeben. Der Grund für die
Unleserlichkeit wird im `@reason`-Attribut
wiedergegeben, die Sicherheit der Rekonstruktion steht im
`@cert`-Attribut. Folgende Werte können die Attribute
`@reason` und `@cert` dabei annehmen:

| Element | Attribut | Wert | Bedeutung |
| --- | --- | --- | --- |
| `<supplied>` | `@reason` | `damage` | durch Schäden am Original verloren |
| `covered` | durch Überschreibung/Überzeichnung unleserlich |
| `@cert` | `high` | hohe Sicherheit der Lesart |
| `low` | geringe Sicherheit der Lesart |


---

## Verantwortlichkeiten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msEditorResp.html](https://www.deutschestextarchiv.de/doku/basisformat/msEditorResp.html)

# Verantwortlichkeiten

Editorische Entscheidungen können mittels eines
`@resp`-Attributs einem Editor zugewiesen werden. Der
Wert des `@resp`-Attributs ist dabei ein Identifier
als Verweis, welcher im `<teiHeader>` aufgelöst
wird.

Das Attribut `@resp` kann dabei in den Elementen
`<persName>`,
`<placeName>`,
`<orgName>`, `<name>`,
`<unclear>`, `<supplied>`,
`<reg>`, `<corr>`,
`<expan>` verwendet werden.

**Beispiele:**

```
<choice>
  <sic>[originale, fehlerhafte Schreibweise]</sic>
  <corr resp="#[Bearbeiter-ID]">[korrigierte Schreibweise]</corr>
</choice>
```

```
<supplied resp="#[Bearbeiter-ID]">[gegenüber der Vorlage ergänzte Zeichenkette]</supplied>
```


---

## Einweisung einer Hinzufügung in den Text

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msEinweisung.html](https://www.deutschestextarchiv.de/doku/basisformat/msEinweisung.html)

# Einweisung einer Hinzufügung in den Text

Wird eine Hinzufügung in den Text eingewiesen (durch Pfeil, Referenzzeichen, o. ä.),
so wird durch das Element `<metamark/>` auf das jeweilige
Einweisungszeichen hingewiesen. Das Element `<metamark/>` ist
dabei ein leeres Element, welches innerhalb des `<add>`-Elements
steht.

```
<add><metamark/>[Hinzufügung]</add>
```

VORSICHT:

Die genaue Ausführung des Einweisungszeichen wird **nicht** näher beschrieben.


---

## Seiten- und Blattnummerierung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msFoliierung.html](https://www.deutschestextarchiv.de/doku/basisformat/msFoliierung.html)

# Seiten- und Blattnummerierung

Seitenumbrüche werden entsprechend den [DTABf-Richtlinien für die
Auszeichnung von Seitenzahlen](seitenFacsNr.html) wie folgt erfasst:

```
<pb facs="#f[Bildnummer]" n="[Seitenzahl]"/>
```

Auch wenn das Manuskript nicht selbst paginiert ist, steht dennoch immer das
`<pb>`-Element, das im `@facs`-Attribut die Faksimilenummer enthält.

Ist das Manuskript darüber hinaus foliiert, so wird die Folionummer im
`<fw>`-Element wiedergegeben, welches das Attribut-Wert-Paar
`@type="folNum"` enthält.

```
<fw type="folNum">[Blattzahl]</fw>
```


---

## Besonderheiten der Kapitelstruktur

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msKapitel.html](https://www.deutschestextarchiv.de/doku/basisformat/msKapitel.html)

# Besonderheiten der Kapitelstruktur

## Kapitel

Kapitel in Manuskripten werden mit dem Element `<div>` umschlossen. Dabei kann das `@type`-Attribut
neben den im DTABf erlaubten Werten zusätzliche Werte für manuskripttypische Textsorten enthalten:

| `@type` | Bedeutung |
| --- | --- |
| `session` | Mitschrift einer Vorlesungsstunde |
| `letter` | Brief |

```
<div type="session">[Mitschrift einer Vorlesungsstunde]</div>
```

## Titel

Ist der Titel eines Kapitels im Manuskript am Rand eingetragen, so erhält das Element
`<head>` ein `@type`-Attribut, welches die Werte `"leftMargin"`
(Eintragung am linken Rand) oder `"rightMargin"` (Eintragung am rechten Rand) erhalten kann.

```
<head type="leftMargin">[Titel am linken Blattrand]</head>
```

```
<head type="rightMargin">[Titel am rechten Blattrand]</head>
```


---

## Besonderheiten bei den Metadaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msMetadata.html](https://www.deutschestextarchiv.de/doku/basisformat/msMetadata.html)

# Besonderheiten bei den Metadaten

Die Metadaten erhalten zusätzlich zu den
[DTA-Metadaten-Richtlinien](metadaten.html "Erfassung (Transkription) und Auszeichnung von Metadaten")
weitere Manuskript-spezifische Elemente.

Das Element [`<bibl>`
der Source Description](mdSdBibl.html) erhält den `@type`-Wert `"MAN"` für Manuskripte.

Die Manuscript Description enthält bei Manuskripten das Element `<handDesc>`,
welches die Hände des Manuskripts in jeweils einem `<handNote>`-Element beschreibt.
Das Element `<handNote>` erhält dabei eine @xml:id, in welcher die jeweilige
Hand eindeutig identifiziert wird. Auf diesen Identifier kann im Text mittels des @hand-Attributs
verwiesen werden.


---

## Platzhalter des Autors

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msPlatzhalter.html](https://www.deutschestextarchiv.de/doku/basisformat/msPlatzhalter.html)

# Platzhalter des Autors

Ein Leerraum im Fließtext, der vom Autor für spätere Hinzufügungen gelassen worden ist,
wird mit dem `<space>`-Element wiedergegeben. Zur Angabe des genauen Umfangs, den
der Leerraum einnimmt, stehen die Attribute `@unit` (Einheit, in welcher der
Umfang angegeben wird) und `@quantity` (Umfang des Leerraums) zur Verfügung.
Folgende Werte kann das Attribut `@unit` dabei annehmen:

| `@unit`-Wert | Bedeutung |
| --- | --- |
| `chars` | Zeichen |
| `words` | Wörter, i. e. Tokens |
| `lines` | Zeilen |
| `pages` | Seiten |

Der Inhalt des `@quantity`-Attributs ist stets eine Zahl.


---

## Wiedergabe von Bibliotheksstempeln

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msStamp.html](https://www.deutschestextarchiv.de/doku/basisformat/msStamp.html)

# Wiedergabe von Bibliotheksstempeln

Enthält das Manuskript Bibliotheksstempel als Besitzvermerke, so werden diese
im `<figure>`-Element wiedergegeben, welches das Attribut-Wert-Paar
`@type="stamp"` enthält.


---

## Substitutionen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/msSubst.html](https://www.deutschestextarchiv.de/doku/basisformat/msSubst.html)

# Substitutionen

Ersetzt der Bearbeiter eine Tilgung durch die Hinzufügung eines Textstücks, so werden die
Elemente `<add>` und `<del>` von einem
`<subst>`-Element (für Substitution) umschlossen.

```
<subst>
  <del>[Tilgung]</del>
  <add>[Ersetzung]</add>
</subst>
```

VORSICHT:

Das Element `<subst>` wird **nicht** verwendet,
wenn eine ursprüngliche Hinzufügung ihrerseits getilgt wurde.


---

## Mehrzeilige Zellen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/mzZellen.html](https://www.deutschestextarchiv.de/doku/basisformat/mzZellen.html)

# Mehrzeilige Zellen

Erstreckt sich eine Zelle (`<cell>`) über mehrere Zeilen und/oder
Spalten kann sie mit den Attributen `@cols` (für Spalten) und
`@rows` (für Zeilen) versehen werden. Der jeweilige Wert ist die Menge an
Zeilen/Spalten, über die sich die Zelle erstreckt:

```
<cell cols="[Spaltenanzahl]" rows="[Zeilenanzahl]">...</cell>
```


---

## Nachsatz

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/nachsatz.html](https://www.deutschestextarchiv.de/doku/basisformat/nachsatz.html)

# Nachsatz

Ein Nachsatz am Schluss eines Kapitels oder des Buchtextes wird
mittels des `<trailer>`- Elements
gekennzeichnet:

```
<trailer>[Nachsatz]</trailer>
```

## Kodierung eines Nachsatzes

![](img/CLzL3jCwSr.png)

```
<p>Von der Mutter hab’ ich die beſten Nachrichten.</p><lb/>
<closer>
  <signed>Bettine.</signed><lb/>
</closer>
<trailer>Ende des erſten Bandes.</trailer><lb/>
```

*Quelle: [Arnim, Bettina von: Goethe's
Briefwechsel mit einem Kinde. Bd. 1. Berlin, 1835. [Faksimile
388]](http://www.deutschestextarchiv.de/arnimb_goethe01_1835/388)*


---

## Normalisierungen historischer Schreibungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/normalisierung.html](https://www.deutschestextarchiv.de/doku/basisformat/normalisierung.html)

# Normalisierungen historischer Schreibungen

Sämtliche historischen Schreibungen werden vorlagengetreu übernommen, d.h., sie werden nicht
stillschweigend modernisiert. Moderne oder anderweitig normalisierte Äquivalente historischer
Schreibungen können jedoch vermerkt werden. Hierfür steht das Element `<choice>`
mit den Unterelementen `<orig>` (historische Schreibung entsprechend der Vorlage)
und `<reg>` (modernisierte/normalisierte Schreibung) zur Verfügung.

```
<choice>
  <orig>[Historische Schreibung entsprechend der Vorlage]</orig>
  <reg>[Korrespondierende normalisierte Schreibung]</reg>
</choice>
```

Soll eine ungewöhnliche Schreibung der Vorlage nur als solche markiert werden ohne Angabe
der zugehörigen modernisierten Form, so wird das Element `<orig>` gesetzt.
Die Elemente `<choice>` und `<reg>` entfallen in diesem Fall.

```
<orig>[Schreibung entsprechend der Vorlage]</orig>
```

VORSICHT:

Eine Normalisierung kann jedoch nie ohne die zugehörige, aus der Vorlage entnommene
originale Form stehen (d.h. stillschweigende Modernisierungen historischer Schreibungen
sind unzulässig). Das Element `<reg>` kann somit nie ohne zugehöriges
`<choice>` und `<orig>` stehen.


---

## Notenbeispiele

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/noten.html](https://www.deutschestextarchiv.de/doku/basisformat/noten.html)

# Notenbeispiele

Notenbeispiele werden als eine Spezialform der Abbildung behandelt und mittels
`<figure>` ausgezeichnet. Zur eindeutigen Kennzeichnung kann das
`<figure>`-Element durch das Attribut `@type` mit dem
Wert `"notatedMusic"` spezifiziert werden.

```
<figure type="notatedMusic"/>
```

## Kodierung von Notenbeispielen

![](img/hlml01CtE1.png)

```
<p>
  Wann drey <hi rendition="#aq">Breves</hi> aneinander gehengt<lb/>
  werden/ vnd die erſte jhre <hi rendition="#aq">Liniam</hi> auffwarts<lb/>
  kehret/ gilt die letzte <hi rendition="#i">2.</hi> ſchla&#x0364;ge.
</p><lb/>
<figure type="notatedMusic">
  <head><hi rendition="#aq">Exemplum.</hi></head>
</figure><lb/>
```

*Quelle: [Friderici, Daniel: Musica Figuralis, Oder Newe
Klärliche Richtige/ vnd vorstentliche vnterweisung/ Der SingeKunst. Rostock, 1619.
[Faksimile 17]](http://www.deutschestextarchiv.de/friderici_musica_1619/17)*


---

## Grundstruktur der Kodierung von Orientierungshilfen im Buchblock

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/ohAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/ohAllg.html)

# Grundstruktur der Kodierung von Orientierungshilfen im Buchblock

Orientierungshilfen wie Kolumentitel, Bogensignatur und Kustoden werden mit dem
Element `<fw>` ausgezeichnet. Dieses enthält die Attribute
`@type` zur Angabe der Art der Orientierungshilfe und `@place` zur
Angabe der Position auf der Seite.


---

## Orientierungshilfen im Buchblock (Kolumnentitel, Bogensignatur, Kustode)

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/orientierungshilfen.html](https://www.deutschestextarchiv.de/doku/basisformat/orientierungshilfen.html)

# Orientierungshilfen im Buchblock (Kolumnentitel, Bogensignatur, Kustode)

## Themen

* [Orientierungshilfen Grundstruktur](ohAllg.html)
* [Lebende Kolumnentitel](kolumnentitel.html)
* [Bogensignaturen und Kustoden](bogensigKustode.html)


---

## Eigenständige Textpassagen korrespondieren inhaltlich miteinander

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/parallelePassagen.html](https://www.deutschestextarchiv.de/doku/basisformat/parallelePassagen.html)

# Eigenständige Textpassagen korrespondieren inhaltlich miteinander

Bei eigenständigen Textpassagen, die inhaltlich miteinander korrespondieren, jedoch nicht
in linearer Reihenfolge angeordnet sind (z.B. fremdsprachliche Texte und deren Übersetzung),
erfolgt die Verknüpfung durch das Attribut `@corresp` unter Zuhilfenahme von `@xml:id`'s.

```
<div xml:id="[ID text01_teil01]" corresp="#[ID text01_teil02]">[...]</div>
<pb facs="#f[Faksimilenummer]"/>
<div xml:id="[ID text01_teil02]" corresp="#[ID text01_teil01]">[...]</div>
```


---

## Publikationen zum DTA-Basisformat

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/publikationen](https://www.deutschestextarchiv.de/doku/basisformat/publikationen)

# Publikationen zum DTA-Basisformat

* Zum DTABf:

  Susanne Haaf, Alexander Geyken, Frank Wiegand: *The DTA “Base Format”: A TEI Subset for the Compilation of a Large Reference Corpus of Printed Text from Multiple Sources.* In: Journal of the Text Encoding Initiative 8, 2014/15. [Online-Version](http://jtei.revues.org/1114), DOI: 10.4000/jtei.1114.Alexander Geyken, Susanne Haaf, Frank Wiegand: *The DTA ‘base format’: A TEI-Subset for the Compilation of Interoperable Corpora.* In: 11th Conference on Natural Language Processing (KONVENS) – Empirical Methods in Natural Language Processing, Proceedings of the Conference. Edited by Jeremy Jancsary. Wien, 2012 (= Schriftenreihe der Österreichischen Gesellschaft für Artificial Intelligence 5). [Online-Version](http://www.oegai.at/konvens2012/proceedings/57_geyken12w/57_geyken12w.pdf).
* Zum DTABf für Zeitungen:

  Susanne Haaf, Matthias Schulz: *Historical Newspapers & Journals for the DTA.* In: Language Resources and Technologies for Processing and Linking Historical Documents and Archives – Deploying Linked Open Data in Cultural Heritage – LRT4HDA. Proceedings of the workshop, held at the Ninth International Conference on Language Resources and Evaluation (LREC'14), May 26–31, 2014, Reykjavik (Iceland), p. 50–54. [Online-Version](http://www.lrec-conf.org/proceedings/lrec2014/workshops/LREC2014Workshop-LRT4HDA%20Proceedings.pdf#page=57).
* Zum DTABf für Manuskripte:

  Susanne Haaf, Christian Thomas: *Introducing the DTABf-M: A Manuscript-specific Extension to the DTA ›Base Format‹ (DTABf).* [In Review; eingereicht für jTEI 10]
* Zu Analysemöglichkeiten in Korpora auf Grundlage des TEI(DTABf)-Tagging:

  Susanne Haaf: *Corpus Analysis based on Structural Phenomena in Texts: Exploiting TEI Encoding for Linguistic Research.* LREC 2016. [Im Erscheinen, vorgesehen für die "Proceedings of the Tenth International Conference on Language Resources and Evaluation (LREC'16)"]


---

## Publikationen zum DTA-Basisformat

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/publikationen.html](https://www.deutschestextarchiv.de/doku/basisformat/publikationen.html)

# Publikationen zum DTA-Basisformat

* Zum DTABf:

  Susanne Haaf, Alexander Geyken, Frank Wiegand: *The DTA “Base Format”: A TEI Subset for the Compilation of a Large Reference Corpus of Printed Text from Multiple Sources.* In: Journal of the Text Encoding Initiative 8, 2014/15. [Online-Version](http://jtei.revues.org/1114), DOI: 10.4000/jtei.1114.Alexander Geyken, Susanne Haaf, Frank Wiegand: *The DTA ‘base format’: A TEI-Subset for the Compilation of Interoperable Corpora.* In: 11th Conference on Natural Language Processing (KONVENS) – Empirical Methods in Natural Language Processing, Proceedings of the Conference. Edited by Jeremy Jancsary. Wien, 2012 (= Schriftenreihe der Österreichischen Gesellschaft für Artificial Intelligence 5). [Online-Version](http://www.oegai.at/konvens2012/proceedings/57_geyken12w/57_geyken12w.pdf).
* Zum DTABf für Zeitungen:

  Susanne Haaf, Matthias Schulz: *Historical Newspapers & Journals for the DTA.* In: Language Resources and Technologies for Processing and Linking Historical Documents and Archives – Deploying Linked Open Data in Cultural Heritage – LRT4HDA. Proceedings of the workshop, held at the Ninth International Conference on Language Resources and Evaluation (LREC'14), May 26–31, 2014, Reykjavik (Iceland), p. 50–54. [Online-Version](http://www.lrec-conf.org/proceedings/lrec2014/workshops/LREC2014Workshop-LRT4HDA%20Proceedings.pdf#page=57).
* Zum DTABf für Manuskripte:

  Susanne Haaf, Christian Thomas: *Introducing the DTABf-M: A Manuscript-specific Extension to the DTA ›Base Format‹ (DTABf).* [In Review; eingereicht für jTEI 10]
* Zu Analysemöglichkeiten in Korpora auf Grundlage des TEI(DTABf)-Tagging:

  Susanne Haaf: *Corpus Analysis based on Structural Phenomena in Texts: Exploiting TEI Encoding for Linguistic Research.* LREC 2016. [Im Erscheinen, vorgesehen für die "Proceedings of the Tenth International Conference on Language Resources and Evaluation (LREC'16)"]


---

## Titelseite einer Reihe und zugehörige Haupttitelseite

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/reihentitel.html](https://www.deutschestextarchiv.de/doku/basisformat/reihentitel.html)

# Titelseite einer Reihe und zugehörige Haupttitelseite

## Kodierung von Titelblättern in Reihen – Reihentitel

![](img/OmeADwUbxh.png)

```
<titlePage type="series">
  <docTitle>
    <titlePart type="main">
      <hi rendition="#g">Die<lb/><hi rendition="#b">Wunder des Himmels,</hi><lb/>
      oder</hi><lb/>
      <hi rendition="#b">gemeinfaßliche Darſtellung</hi><lb/>
      <hi rendition="#g">des<lb/><hi rendition="#b">Weltſyſtems.</hi></hi>
    </titlePart>
  </docTitle><lb/>
  <byline>
    <hi rendition="#g">Von</hi><lb/>
    <docAuthor><hi rendition="#g">J. J. Littrow</hi></docAuthor>,<lb/>
    Director der k. k. Sternwarte in Wien.
  </byline><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <imprimatur>
    <hi rendition="#g">Mit Königl. Würtembergiſchem Privilegium.</hi>
  </imprimatur><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <titlePart type="desc">
    <hi rendition="#g">Drei Bände</hi>.<lb/>
    Mit dem Bildniſſe des Verfaſſers und aſtronomiſchen Tafeln.
  </titlePart><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <titlePart type="volume">
    <hi rendition="#g">Erſter Theil: Theoriſche Aſtronomie</hi>.
  </titlePart><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <docImprint><hi rendition="#g">Stuttgart</hi>,<lb/>
    <publisher><hi rendition="#g">Carl Hoffmann</hi>.</publisher><lb/>
    <docDate><hi rendition="#g">1834</hi>.</docDate>
  </docImprint><lb/>
</titlePage>
```

Quelle: [Littrow, Joseph Johann von: Die Wunder des Himmels, oder gemeinfaßliche Darstellung des Weltsystems. Bd. 1. Stuttgart, 1834. [Faksimile 10]](http://www.deutschestextarchiv.de/littrow_weltsystem01_1834/10)

## Kodierung von Titelblättern in Reihen – Haupttitelseite

![](img/xVE55djoI1.png)

```
<titlePage type="main">
  <docTitle>
    <titlePart type="main">
      <hi rendition="#b">Theoriſche Aſtronomie</hi><lb/>
      <hi rendition="#g">oder<lb/>
      <hi rendition="#b">allgemeine Erſcheinungen</hi><lb/>
      des<lb/><hi rendition="#b">Himmels.</hi></hi>
    </titlePart>
  </docTitle><lb/>
  <byline>
    Von<lb/>
    <docAuthor><hi rendition="#g #b">J. J. Littrow,</hi></docAuthor><lb/>
    Director der k. k. Sternwarte in Wien.
  </byline><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <titlePart type="desc">
    Mit dem Bildniſſe des Verfaſſers und aſtronomiſchen Tafeln.
  </titlePart><lb/>
  <milestone rendition="#hr" unit="section"/><lb/>
  <docImprint>
    <pubPlace><hi rendition="#g">Stuttgart</hi>,</pubPlace><lb/>
    <publisher><hi rendition="#g">Carl Hoffmann</hi>.</publisher><lb/>
    <docDate><hi rendition="#g">1834</hi>.</docDate><lb/>
  </docImprint><lb/>
</titlePage>
```

*Quelle: [Littrow,
Joseph Johann von: Die Wunder des
Himmels, oder gemeinfaßliche Darstellung
des Weltsystems. Bd. 1. Stuttgart, 1834.
[Faksimile 11]](http://www.deutschestextarchiv.de/littrow_weltsystem01_1834/11)*


---

## Editorischer Sachkommentar

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/sachkommentar.html](https://www.deutschestextarchiv.de/doku/basisformat/sachkommentar.html)

# Editorischer Sachkommentar

Editorische Sachkommentare können einem Text auf zweierlei Arten beigegeben werden.

**a) im Text, punktuell:** Für editorische Sachkommentare im Text steht das Element
`<note type="editorial">` zur Verfügung. Dieses kann direkt im Anschluss an die Textstelle,
die den Kommentar verlangt, angebracht werden. Innerhalb von `<note type="editorial">`
wird **kein** Material der Quelle wiedergegeben.

```
<p>[...]
  <note type="editorial">[Kommentar]</note>
  [...]
</p>

```

**b) im Text, bezogen auf eine bestimmte Textpassage:** Soll eine Textpassage markiert werden,
auf die sich der editorische Kommentar bezieht, so wird diese mit dem Element `<ref>`
umschlossen, welches das Attribut-Wert-Paar `@type="editorialNote"` erhält. Die Verknüpfung
zwischen der Textstelle und dem zugehörigen editorischen Sachkommentar wird mittels der Attribute
`@xml:id` und `@corresp` realisiert.

```
<p>[...]
  <ref type="editorialNote" xml:id="[ID-Textstelle]" corresp="#[ID-Kommentar]">[Textstelle]</ref>
  <note type="editorial" xml:id="[ID-Kommentar]" corresp="#[ID-Textstelle]">[Kommentar]</note>
  [...]
</p>

```

**c) außerhalb des Textes, punktuell:** Editorische Sachkommentare zum Text, die
außerhalb desselben unter einer eindeutig referenzierbaren Adresse (URI) zugänglich sind, werden
an der betreffenden Textstelle verlinkt. Dabei wird die entsprechende Textstelle mittels
`<ref type="editorialNote">` umschlossen, welches ein `@target`-Attribut
erhält, in dem die URL des Kommentars angegeben wird.

```
<p>[...]
  <ref type="editorialNote" target="[URL-Kommentar]">[Textstelle]</ref>
  [...]
</p>

```

**d) außerhalb des Textes, bezogen auf eine bestimmte Textpassage:** Soll der editorische
Sachkommentar punktuell im Text verlinkt werden, ohne dass eine konkrete Textpassage damit verknüpft
ist, so bleibt das <ref>-Element leer.

```
<p>[...]
  <ref type="editorialNote" target="[URL-Kommentar]"/>
  [...]
</p>

```


---

## Schema und Dokumentation

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/schema.html](https://www.deutschestextarchiv.de/doku/basisformat/schema.html)

# Schema und Dokumentation

Das Schema und die Dokumentation sind unter den im Folgenden aufgeführten Links erreichbar.
Eine Einführung in das Arbeiten mit dem DTA-Basisformat bietet das Kapitel [HowTo](howto.html).

## Das DTABf-Schema

* [RNG-Schema des DTABf für Drucke ⇗](http://www.deutschestextarchiv.de/basisformat.rng)
* [ODD des DTABf für Drucke ⇗](http://www.deutschestextarchiv.de/basisformat.odd)
* [RNG-Schema des DTABf für Manuskripte ⇗](http://www.deutschestextarchiv.de/basisformat_ms.rng)
* [ODD des DTABf für Manuskripte ⇗](http://www.deutschestextarchiv.de/basisformat_ms.odd)
* [Schematron Regelsatz des DTABf ⇗](http://www.deutschestextarchiv.de/basisformat.sch)
* [Hinweise zur Verwendung des Schemas ⇗](benutzungDTABfSchema.html)

Die Fassungen des DTABf-Schemas wurden mithilfe des Chaining-ODDs-Mechanismus erstellt, der durch die Text Encoding Initiative bereitgestellt wird.
Das zugrundeliegende ODD ist unter dem folgenden Link zugänglich:
[DTABf\_all-ODD ⇗](http://www.deutschestextarchiv.de/basisformat_all.odd)

## Komponenten der DTABf-Dokumentation

* Einführung und erste Schritte [[nächstes Kapitel ⇗](ziel.html)]
* [DTABf: Strukturierung der Metadaten ⇗](metadaten.html "Erfassung (Transkription) und Auszeichnung von Metadaten")
* [Richtlinien zur Texterfassung ⇗](transkription.html "Richtlinien zur Erfassung der Volltexte")
* [DTABf: Formale Erschließung der Texte ⇗](texterschliessung_formal.html "Auszeichnung von formalen Strukturen in Volltexten (Besonderheiten in Typographie und Layout)")
* [DTABf: Inhaltliche Erschließung der Texte ⇗](texterschliessung_inhaltlich.html "Auszeichnung von inhaltsbezogenen (logischen, konzeptuellen) Strukturen in Volltexten")
* Besondere Textsorten
  + [DTABf: Auszeichnung von
    Manuskripten ⇗](manuskript.html)
  + [DTABf: Auszeichnung von
    Zeitungen ⇗](zeitung.html)
* Übersichten
  + [Übersicht über alle Basisformat-Elemente im `<teiHeader>`-Bereich ⇗](uebersichtHeader.html)
  + [Übersicht über alle Basisformat-Elemente im `<text>`-Bereich ⇗](uebersichtText.html)
* [Vorlagedatei zum DTA-Basisformat ⇗](http://www.deutschestextarchiv.de/files/vorlage_basisformat.xml)


---

## Schriftartwechsel

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/schriftart.html](https://www.deutschestextarchiv.de/doku/basisformat/schriftart.html)

# Schriftartwechsel

## Themen

* [Schriftartwechsel Grundstruktur](schriftartAllg.html)
* [Frakturwechsel](frakturwechsel.html)
* [Wechsel zur Antiquaschrift](wechselAntiqua.html)


---

## Grundstruktur der Kodierung von Schriftartwechsel

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/schriftartAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/schriftartAllg.html)

# Grundstruktur der Kodierung von Schriftartwechsel

Unterschiedliche Schriftgrößen werden nicht gesondert gekennzeichnet.
Schriftartwechsel wird hingegen wie folgt ausgezeichnet:

| Attribut-Wert-Paar | Bedeutung |
| --- | --- |
| `rendition="#fr"` | Wechsel zwischen unterschiedlichen Frakturtypen |
| `rendition="#aq"` | Wechsel von Fraktur- zu Antiquaschrift |


---

## Sperrdruck über das Zeilenende hinaus

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/sdMehrzeilig.html](https://www.deutschestextarchiv.de/doku/basisformat/sdMehrzeilig.html)

# Sperrdruck über das Zeilenende hinaus

## Sperrdruck am Zeilenumbruch

![](img/wdNlu1NyWu.png)

```
<hi rendition="#g">Di-<lb/>luvium</hi>
```

*Quelle: [Schleiden, Matthias Jacob: Das Alter des
Menschengeschlechts, die Entstehung der Arten und die Stellung des Menschen in
der Natur. Leipzig, 1863. [Faksimile 19]](http://www.deutschestextarchiv.de/schleiden_menschengeschlecht_1863/19)*


---

## Wechsel zwischen gesperrt und nicht-gesperrt innerhalb eines Wortes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/sdWechsel.html](https://www.deutschestextarchiv.de/doku/basisformat/sdWechsel.html)

# Wechsel zwischen gesperrt und nicht-gesperrt innerhalb eines Wortes

## Normal- und Sperrdruck in einem Wort

![](img/EzB7q6t3my.png)

```
das <hi rendition="#g">Berg-</hi>, <hi rendition="#g">Hütten-</hi> 
und <hi rendition="#g">Salinen</hi>fach
```

*Quelle: [Stein, Lorenz von: Die Verwaltungslehre. Bd. 5.
Stuttgart, 1868. [Faksimile 309]](http://www.deutschestextarchiv.de/book/view/stein_verwaltungslehre05_1868?p=309)*


---

## Seitenzahlen und Bildnummern

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/seitenFacsNr.html](https://www.deutschestextarchiv.de/doku/basisformat/seitenFacsNr.html)

# Seitenzahlen und Bildnummern

Seitenzahlen der Vorlage und die fortlaufenden Nummern der zugehörigen Digitalisate werden
wie folgt wiedergegeben:

```
<pb facs="#f[Bildnummer]" n="[Seitenzahl]"/>
```

Die Seitenzahlen werden jeweils zu Beginn einer Seite eingefügt, auch wenn die Seitenzahl
unter dem Text steht. Fehlt die Seitenzahl im Original (z.B. unpaginierte Abbildungsseiten
oder vor neuen Kapiteln), wird entsprechend der Zählung im Buch die Seitenzahl in eckigen
Klammern ergänzt:

```
<pb facs="#f[Bildnummer]" n="[[Seitenzahl]]"/>
```

Ist eine Seitenzahl falsch gedruckt, wird die falsche Seitenzahl abgetippt. Die korrigierte
Seitenzahl steht mit im @n-Attribut in eckigen Klammern. Die korrekte Ordnung der Seiten im
Band wird durch die Bildnummern vermittelt, die fehlerfrei fortlaufend angegeben werden.

```
<pb facs="#f[Bildnummer]" n="[fehlerhafte Seitenzahl [korrigierte Seitenzahl]]"/>
```

Besonderheiten bei Seitenzahlen wie etwa Verzierungen oder Einklammerungen werden nicht
wiedergegeben.

## Seitenzahl

![](img/atgLm3hoFa.png)

```
<pb facs="#f0188" n="180"/>
```

*Quelle: [Humboldt, Alexander von: Reise in die
Aequinoktial-Gegenden des neuen Kontinents. Bd. 4. Übers. v. Hermann Hauff. Stuttgart,
1860, facs. 188.](http://www.deutschestextarchiv.de/humboldt_aequinoktial04_1859/188)*

## Seitenzahl mit Verzierung

![](img/bNimbug0NC.png)

```
<pb facs="#f0014" n="8"/>
```

*Quelle: [Campe, Joachim Heinrich: Robinson der Jüngere. Bd. 2.
Hamburg, 1780, facs. 14.](http://www.deutschestextarchiv.de/campe_robinson02_1780/14)*

Um eine im DTA herausgegebene Textseite mit einem externen Äquivalent zu verknüpfen
(z.B. mit der entsprechenden Seite der Quelle in einer anderen digitalen Edition) wird das
`@corresp`-Attribut innerhalb des `<pb>`-Elements
verwendet. Als Wert in `@corresp` steht eine eindeutige URI, welche zu dem
verlinkten Dokument führt.

## Seitenzahl extern

![](img/cn4pfRfHOR.png)

```
<front>
  <pb corresp="http://brema.suub.uni-bremen.de/grenzboten/periodical/pageview/179388" facs="#f0005"/>
  <titlePage type="main"> 
    <titlePart type="main"> 
      <hi rendition="#b"><hi rendition="#g">Die<lb/>Grenzboten</hi>.</hi> 
    </titlePart>
  </titlePage>
</front>
```

*Quelle: [Die Grenzboten. Erster Jahrgang. Leipzig, 1841.
[Faksimile 5]](http://www.deutschestextarchiv.de/grenzboten_179382_282158/5)*

Der Ort, an welchem die Seitenzahl auf der Seite platziert ist, sowie die Art der
Ausschmückung der Seitenangabe wird in der Regel nicht mit dokumentiert. Soll diese
Information jedoch in der Transkription berücksichtigt werden (Level 3), so wird hierfür der
folgende Ausdruck verwendet:

```
<fw type="pageNum" place="top">[Seitenzahl oben]</fw>
<fw type="pageNum" place="bottom">[Seitenzahl unten]</fw>
```


---

## Silbentrennung am Zeilenumbruch

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/silbentrennung.html](https://www.deutschestextarchiv.de/doku/basisformat/silbentrennung.html)

# Silbentrennung am Zeilenumbruch

Silbentrennungen am Zeilenumbruch werden beibehalten. Als Silbentrennstrich steht,
ungeachtet des Erscheinungsbildes im Text, der Bindestrich (`&#x002D;`).

HINWEIS:

***Abweichende Regelung Phase 1:** Eine Ausnahme bilden die durch OCR erfassten Texte, in welchen
zwischen dem bedingten Trennstrich (`&#x00AC;`) und dem Bindestrich
(`&#x002D;`) unterschieden wird.*


---

## Spalten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/spalte.html](https://www.deutschestextarchiv.de/doku/basisformat/spalte.html)

# Spalten

Spaltenumbrüche werden mittels `<cb/>` ausgezeichnet. Dabei markiert
das `<cb>`-Element jeweils den Beginn einer neuen Spalte.
Spaltenzählung wird durch ein `@n`-Attribut innerhalb von
`<cb>` wiedergegeben.

Verschiedene Erscheinungsformen von Spalten sind möglich:

a) Der Text eines Bandes ist gänzlich in Spalten organisiert: In diesen Fällen ist in
der Vorlage die Seitennummerierung in der Regel durch Spaltenzählung ersetzt. Die
jeweilige Spaltennummer wird in der Transkription innerhalb des
`<cb>`-Elements als Wert des `@n`-Attributs wiedergegeben. Die
Seitenzählung wird daneben im `@n`-Attribut innerhalb des
`<pb>`-Elements rekonstruiert. Wechseln sich im Band gezählte und
ungezählte Spalten ab, so werden die fehlenden Spaltennummern nicht rekonstruiert. Es
wird jedoch fortlaufend eine (ggf. rekonstruierte) Seitenzählung beibehalten.

```
<pb facs="#f[Bildnummer]" n="[[rekonstruierte Seitenzahl]]"/><cb n="[Spaltenzahl]"/>
```

oder:

```
<pb facs="#f[Bildnummer]" n="[[rekonstruierte Seitenzahl]]"/><cb/>
```

b) Der Text eines Bandes ist seitenweise organisiert, wird jedoch gelegentlich durch
Spaltendruck unterbrochen. In diesem Fall wird der Beginn des Spaltensatzes mittels `<cb type="start"/>`,
das Ende des Spaltensatzes analog mittels `<cb type="end"/>` gekennzeichnet. Spaltenumbrüche innerhalb des Spaltensatzes werden
mittels des leeren `<cb>`-Elements wiedergegeben.

HINWEIS:

***Abweichende Regelung Phase 1:** b) Der Text eines Bandes ist seitenweise organisiert, wird jedoch gelegentlich durch
Spaltendruck unterbrochen. In diesem Fall steht ein leeres `<cb>`-Element am Beginn jeder Spalte.*

c) Fußnoten- oder Endnotentext, Register und Verzeichnisse sind in Spalten gesetzt. Auch hier wird der Beginn des Spaltensatzes mittels `<cb type="start"/>`,
das Ende des Spaltensatzes analog mittels `<cb type="end"/>` gekennzeichnet. Spaltenumbrüche innerhalb des Spaltensatzes werden
wiederum mittels des leeren `<cb>`-Elements wiedergegeben.

HINWEIS:

***Abweichende Regelung Phase 1:** c) Fußnoten- oder Endnotentext, Register und Verzeichnisse sind in Spalten gesetzt. In diesem Fall markiert ebenfalls ein leeres
`<cb>`-Element den jeweiligen Spaltenbeginn.*


---

## Sperrdruck

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/sperrdruck.html](https://www.deutschestextarchiv.de/doku/basisformat/sperrdruck.html)

# Sperrdruck

## Themen

* [Sperrdruck Grundstruktur](sperrdruckAllg.html)
* [Sperrdruck über das Zeilenende hinaus](sdMehrzeilig.html)
* [Wechsel zwischen gesperrt und nicht-gesperrt innerhalb eines Wortes](sdWechsel.html)


---

## Grundstrucktur der Kodierung von Sperrdruck

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/sperrdruckAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/sperrdruckAllg.html)

# Grundstrucktur der Kodierung von Sperrdruck

**Gesperrt gesetzter Text** wird mit `<hi rendition="#g">`
ausgezeichnet. Satzzeichen innerhalb einer gesperrt gesetzten Passage werden mit einbezogen.
Satzzeichen im Anschluss an gesperrten Text werden vorlagengetreu wiedergegeben. Reicht der
Gesperrtdruck über ein Zeilenende mit Silbentrennstrich hinaus, so wird das
`<hi>`-Element nicht unterbrochen. Sind nur Teile eines Wortes gesperrt, so wird
das `<hi>`-Element innerhalb des Wortes hinter dem letzten gesperrt gedruckten
Zeichen geschlossen.

## Kodierung von Sperrdruck (1)

![](img/c6Z2dCeEBa.png)

```
<hi rendition="#g">Fu&#x0364;rſt</hi>. (<hi rendition="#g">ſehr zornig</hi>)
               
```

*Quelle:
[Spiess, Christian Heinrich: Biographien der Wahnsinnigen. Bd. 4. Leipzig, 1796. [Faksimile 107]](http://www.deutschestextarchiv.de/spiess_biographien04_1796/107)*

## Kodierung von Sperrdruck (2)

![](img/bXwJ1BYndg.png)

```
die <hi rendition="#g">erſte</hi> und <hi rendition="#g">zwar indirecte Selbſterkenntniß</hi>
               
```

*Quelle:
[Feuerbach, Ludwig: Das Wesen des Christentums. Leipzig, 1841. [Faksimile 36]](http://www.deutschestextarchiv.de/feuerbach_christentum_1841/36)*


---

## Weiterentwicklung des Formats

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/steuerungsgruppe.html](https://www.deutschestextarchiv.de/doku/basisformat/steuerungsgruppe.html)

# Weiterentwicklung des Formats

Zunehmend wird das DTABf, das im Projektkontext des DTA entstand, auch von externen Projekten verwendet. Damit steigt der Bedarf, das Format für Kontexte außerhalb des korpuslinguistischen Fokus des DTA zusätzlich nutzbar zu machen. Um dieser Entwicklung gerecht zu werden, wurde eine **Steuerungsgruppe** gegründet, deren Mitglieder durch ihre Verankerung in verschiedenen Communities unterschiedliche Perspektiven und Expertisen bei der Weiterentwicklung des Formats einbringen können.

Die DTABf-Steuerungsgruppe setzt sich aus Expertinnen und Experten für TEI-Auszeichnung und
-Anpassung zusammen. Sie gehörten zum Teil bereits dem ursprünglichen Team des DTA an;
zum Teil repräsentieren sie andere Projekte, die ebenfalls das DTA-Basisformat
einsetzen. Mitglieder sind [Matthias Boenig](https://tboenig.github.io/), [Daniel Burckhardt](https://www.ghi-dc.org/ghi-staff/research-service/daniel-burckhardt.html) (GHI Washington DC), [Stefan Dumont](http://www.bbaw.de/die-akademie/mitarbeiter/dumont) (BBAW, Telota), [Alexander Geyken](http://www.bbaw.de/die-akademie/mitarbeiter/geyken) (BBAW, DWDS & ZDL), [Martina
Gödel](http://textloop.de/werdegang/) (textloop, BBAW), [Susanne Haaf](https://www.uni-leipzig.de/personenprofil/mitarbeiter/susanne-haaf-dumont) (Universität Leipzig), [Axel Herold](http://www.bbaw.de/die-akademie/mitarbeiter/herold) (BBAW, DWDS/ZDL, Text+), [Christian Thomas](http://www.bbaw.de/die-akademie/mitarbeiter/thomas) (BBAW, KSW).

Die DTABf-Steuerungsgruppe trifft sich regelmäßig, um Entwicklungen am DTA-Basisformat abzustimmen und über neue Vorschläge zu entscheiden. Im Fokus stehen dabei die Erweiterungs- und Änderungsvorschläge der Nutzenden, die über Tickets auf der GitHub-Präsenz des DTABf gemeldet werden. Alle Vorschläge werden vor dem Hintergrund der [DTABf-Leitlinien](leitlinien.html) beraten.


---

## Grundstruktur der Kodierung von Tabellen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/tabAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/tabAllg.html)

# Grundstruktur der Kodierung von Tabellen

Tabellen werden mittels des Elements `<table>` ausgezeichnet. Der
Tabelleninhalt wird zeilenweise wiedergegeben (`<row>`). Jede Zeile ist
wiederum in Zellen unterteilt (`<cell>`). Trägt die Tabelle einen Titel,
so wird dieser mit einem `<head>`-Element umschlossen.

```
<table>
  <head>[ggf. Titel der Tabelle]</head><!-- sofern vorhanden -->
  <row>
    <cell>[Text einer Tabellen-Zelle]</cell>
    <cell>[Text einer Tabellen-Zelle]</cell>
  </row>
  ...
</table>
```

Übersichten in Tabellenform, die keinen oder nur wenig reinen Text enthalten (z.B.
vornehmlich aus Zahlen und Sonderzeichen bestehen), werden nicht erfasst. Statt dessen wird
durch eine leere Tabelle auf die jeweilige Übersicht hingewiesen:

```
<table><row><cell/></row></table>
```

## Kodierung von Tabellen (1)

![](img/99U3cgDN24.png)

```
<table>
  <row>
    <cell/>
    <cell>Perſonen</cell>
    <cell>Prozent der Be-<lb/>völkerung</cell>
  </row><lb/>
  <row>
    <cell>in London</cell>
    <cell>2401955</cell>
    <cell>62,9</cell>
  </row><lb/>
  <row>
    <cell>in der nächſten Umgebung</cell>
    <cell>384871</cell>
    <cell>10,1</cell>
  </row><lb/>
  <row>
    <cell>in andern Teilen von Eng-<lb/>land und Wales</cell>
    <cell>787699</cell>
    <cell>20,6</cell>
  </row><lb/>
  <row>
    <cell>in Schottland</cell>
    <cell>49554</cell>
    <cell>1,3</cell>
  </row><lb/>
  <row>
    <cell>in Irland</cell>
    <cell>80778</cell>
    <cell>2,1</cell>
  </row><lb/>
  <row>
    <cell>in andern Ländern</cell>
    <cell>111626</cell>
    <cell>2,9</cell>
  </row><lb/>
</table>
```

*Quelle: [Bücher, Karl: Die Entstehung der Volkswirtschaft. Sechs
Vorträge. Tübingen, 1893. [Faksimile 299]](http://www.deutschestextarchiv.de/buecher_volkswirtschaft_1893/299)*

## Kodierung von Tabellen (2)

![](img/C1lxLceKRU.png)

```
<table>
  <row>
    <cell/>
    <cell>Dauer der<lb/>ganzen<lb/>Periode</cell>
    <cell>Ausweichung<lb/>von der<lb/>Sonne beim<lb/>Stillſtand</cell>
    <cell>Bogen des<lb/>Rückgangs</cell>
    <cell>Dauer des<lb/>Rückgangs</cell>
  </row><lb/>
  <row>
    <cell>Mars</cell>
    <cell>780,<hi rendition="#sub">4</hi> Tage</cell>
    <cell>137 Grade</cell>
    <cell>14 Grade</cell>
    <cell>70 Tage</cell>
  </row><lb/>
  <row>
    <cell>Jupiter</cell>
    <cell>398,<hi rendition="#sub">8</hi></cell>
    <cell>117</cell>
    <cell>10</cell>
    <cell>119</cell>
  </row><lb/>
  <row>
    <cell>Saturn</cell>
    <cell>378,<hi rendition="#sub">0</hi></cell>
    <cell>108</cell>
    <cell>7</cell>
    <cell>136</cell>
  </row><lb/>
  <row>
    <cell>Uranus</cell>
    <cell>369,<hi rendition="#sub">7</hi></cell>
    <cell>102</cell>
    <cell>4</cell>
    <cell>150</cell>
  </row><lb/>
</table>
```

*Quelle: [Littrow, Joseph Johann von: Die Wunder des Himmels,
oder gemeinfaßliche Darstellung des Weltsystems. Bd. 1. Stuttgart, 1834. [Faksimile
228]](http://www.deutschestextarchiv.de/littrow_weltsystem01_1834/228)*

HINWEIS:

Mittels eines `@facs`-Attributs im `table`-Element
kann auf die originale Abbildung der Tabelle verwiesen werden. Dies kann nützlich sein, wenn
komplexe Tabellen aus Effizienzgründen nicht erfasst oder nicht vollständig nachgebildet
werden können.


---

## Tabellen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/tabelle.html](https://www.deutschestextarchiv.de/doku/basisformat/tabelle.html)

# Tabellen

## Themen

* [Tabellen Grundstruktur](tabAllg.html)
* [Zeilen- und Spaltenbenennungen](labels.html)
* [Mehrzeilige Zellen](mzZellen.html)


---

## Grundstruktur des Titelblatts

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/tbAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/tbAllg.html)

# Grundstruktur des Titelblatts

Auf Titelblätter wird innerhalb von `<front>`
mit dem Element `<titlePage>` hingewiesen.

Das Element `<titlePage>` kann ein
`@type`-Attribut enthalten, für welches die folgenden
Werte möglich sind:

| `@type`-Wert | Bedeutung |
| --- | --- |
| `main` | Haupttitelseite |
| `halftitle` | Schmutztitel |
| `series` | Titelseite einer Reihe |

Sämtliche Titelblattinformationen werden innerhalb von
`<titlePage>` realisiert, wobei die Reihenfolge
und Vollständigkeit der Angaben den Gegebenheiten der Vorlage folgt.
Folgende Elemente können innerhalb von
`<titlePage>` stehen:

| Element | Bedeutung | Bemerkung |
| --- | --- | --- |
| `<docTitle>` | Titel des Dokuments |  |
| `<titlePart>` | Teil des Dokumenttitels (Haupttitel, Untertitel, nähere inhaltliche Informationen zum Werk etc.) | innerhalb von `<docTitle>` |
| `<byline>` | Einleitung zu den Angaben zur Verantwortlichkeit für das Dokument |  |
| `<docAuthor>` | Autor des Werks | innerhalb von <byline> |
| `<docImprint>` | Angaben zur Publikation |  |
| `<pubPlace>` | Publikationsort | innerhalb von `<docImprint>` |
| `<publisher>` | Drucker, Herausgeber, Verlag | innerhalb von `<docImprint>` |
| `<docDate>` | Erscheinungsjahr | innerhalb von `<docImprint>`; ggf. mit `@when` für eine normalisierte Datumsangabe nach [ISO 8601](http://www.w3.org/TR/xmlschema-2/#isoformats) (Level 3) |
| `<docEdition>` | Auflage |  |
| `<imprimatur>` | Druckerlaubnis | auch außerhalb von `<titlePage>` im `<front>`-Bereich möglich. |
| `<figure>` | Abbildung | auch in anderen Kontexten möglich; s. Kap. [Abbildungen](abbildung.html) |
| `<epigraph>` | Zitat | mit: `<cit>`, `<quote>`, `<bibl>`; auch in anderen Kontexten möglich; s. Kap. [Zitate und Epigraphe](zitateEpigraphe.html) |

Dem Element `<titlePart>` ist ein `@type`-Attribut zugeordnet, für welches folgende Werte möglich sind:

| `@type`-Wert | Bedeutung | Anmerkung |
| --- | --- | --- |
| `main` | Haupttitel |  |
| `sub` | Untertitel |  |
| `volume` | Bandangabe bei mehrbändigen Werken |  |
| `series` | Titel der Reihe |  |
| `desc` | nähere Beschreibungen zur Zusammensetzung bzw. zu den Inhalten des Werkes |  |
| `price` | Buchpreis | Achtung: Preisangaben außerhalb der Titelseite stehen in `<p>` |
| `copyright` | für Hinweise zum Copyright | neben `<div type="copyright">`; nur für die Titelseite |
| `dedication` | Widmung | neben `<div type="dedication">`; nur für die Titelseite |

HINWEIS:

***Abweichende Regelung Phase 1:** Zusätzliche
mögliche `@type`-Werte sind: `series`
(Reihentitel) und `seriesnumber` (Bandnummer
innerhalb einer Reihe).*


---

## Inhaltszusammenfassung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/teaser.html](https://www.deutschestextarchiv.de/doku/basisformat/teaser.html)

# Inhaltszusammenfassung

Kurze Zusammenfassungen des Kapitelinhalts zu Beginn eines Kapitels
werden mit einem `<argument>`-Tag umschlossen.
Der Text innerhalb von `<argument>` steht
wiederum innerhalb von [Paragraphen](absatz.html)
(`<p>`) oder [Listen](liste.html) (`<list>`).

```
<argument>
  <p>[Inhaltszusammenfassung Fließtext]</p>
</argument>
```

```
<argument>
  <list>[Inhaltszusammenfassung Liste]</list>
</argument>
```

## Kodierung von Kapitelteasern

![](img/deNPXJZEdM.png)

```
<div n="1">
  <head>
    <hi rendition="#b"><hi rendition="#aq">IV.</hi><lb/>
    <hi rendition="#g">Van und die Kurden</hi>.</hi>
  </head><lb/>
  <argument>
    <p>Im armeniſchen Kaſchmir. — Die Stadt Van und ihre Denkmäler. —<lb/>
      Hakkiari, der Neſtorianer-Diſtrict. — Die Kurden und ihre geo-<lb/>
      graphiſche Verbreitung.</p>
  </argument><lb/>
  <p>Von Erzerum, dem großen Handelscentrum Armeniens<lb/>
    laufen die Hauptverkehrsadern radienartig nach allen Richtungen.<lb/>
    [...]</p>
</div><lb/>
```

*Quelle: [Schweiger-Lerchenfeld, Amand von: Armenien. Ein Bild seiner Natur
und seiner Bewohner. Jena, 1878. [Faksimile 125]](http://www.deutschestextarchiv.de/schweiger_armenien_1878/125)*


---

## DTA-Basisformat – Formale Erschließung des Volltextes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/texterschliessung_formal.html](https://www.deutschestextarchiv.de/doku/basisformat/texterschliessung_formal.html)

# DTA-Basisformat – Formale Erschließung des Volltextes

Auszeichnung von formalen Strukturen in Volltexten (Besonderheiten in Typographie und Layout)

## Themen

* [Erscheinungsbild Band](erschBildBand.html)
* [Erscheinungsbild Text](erschBildText.html)


---

## DTA-Basisformat – Inhaltliche Erschließung des Volltextes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/texterschliessung_inhaltlich.html](https://www.deutschestextarchiv.de/doku/basisformat/texterschliessung_inhaltlich.html)

# DTA-Basisformat – Inhaltliche Erschließung des Volltextes

Auszeichnung von inhaltsbezogenen (logischen, konzeptuellen) Strukturen in Volltexten

## Themen

* [Grobstrukturierung Dokument](TEIStruktur.html)
* [Texteinteilung Kapitel](div.html)
* [Einleitende Informationen](front.html)
* [Textkörper](body.html)
* [Anhang](anhang.html)
* [Inhaltliche Inline-Auszeichnungen](inlineAnnotation.html)
* [Editorische Eingriffe](editorEingriff.html)


---

## Tiefstellung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/tiefstellung.html](https://www.deutschestextarchiv.de/doku/basisformat/tiefstellung.html)

# Tiefstellung

## Kodierung von Tiefstellungen

![](img/wHRmLS8BOp.png)

```
[...] auf <hi rendition="#i">b</hi> sitzt ein<lb/> eben solches Rad, 
welches <hi rendition="#i">z</hi><hi rendition="#sub">4</hi> Zähne hat.
```

*Quelle: [Fischer, Hermann: Die Werkzeugmaschinen. Bd. 1:
Die Metallbearbeitungs-Maschinen. [Textband]. Berlin, 1900. [Faksimile
181]](http://www.deutschestextarchiv.de/fischer_werkzeugmaschinen01_1900/181)*


---

## Titelblatt

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/titelblatt.html](https://www.deutschestextarchiv.de/doku/basisformat/titelblatt.html)

# Titelblatt

## Themen

* [Titelblatt Grundstruktur](tbAllg.html)
* [Haupttitelseite](haupttitel.html)
* [Reihentitel](reihentitel.html)


---

## Anführungszeichen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trAnfZeichen.html](https://www.deutschestextarchiv.de/doku/basisformat/trAnfZeichen.html)

# Anführungszeichen

Die Anführungszeichen im Text werden mit den entsprechenden Unicode-Entitäten
abgebildet, damit ihre eindeutige Zuordnung zum Text (linksanschmiegend,
rechtsanschmiegend, oben oder unten) festgelegt wird.

| Zeichen | Entität | Beschreibung |
| --- | --- | --- |
| ‘ | U+2018 | LEFT SINGLE QUOTATION MARK |
| ’ | U+2019 | RIGHT SINGLE QUOTATION MARK |
| ‚ | U+201A | SINGLE LOW-9 QUOTATION MARK |
| ‛ | U+201B | SINGLE HIGH-REVERSED-9 QUOTATION MARK |
| “ | U+201C | LEFT DOUBLE QUOTATION MARK |
| ” | U+201D | RIGHT DOUBLE QUOTATION MARK |
| „ | U+201E | DOUBLE LOW-9 QUOTATION MARK |
| ‟ | U+201F | DOUBLE HIGH-REVERSED-9 QUOTATION MARK |
| ‹ | U+2039 | SINGLE LEFT-POINTING ANGLE QUOTATION MARK |
| › | U+203A | SINGLE RIGHT-POINTING ANGLE QUOTATION MARK |
| « | U+00AB | LEFT-POINTING DOUBLE ANGLE QUOTATION MARK |
| » | U+00BB | RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK |

Für die einfachen und doppelten Anführungszeichen vgl. die Unicode-Tabelle
[General Punctuation](http://www.unicode.org/charts/PDF/U2000.pdf)

Für die französischen Anführungszeichen vgl. die Unicode-Tabelle [Controls
and Latin-1 Supplement](http://www.unicode.org/charts/PDF/U0080.pdf)


---

## Anmerkung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trAnmerkung.html](https://www.deutschestextarchiv.de/doku/basisformat/trAnmerkung.html)

# Anmerkung

Für einige Texte aus der 1. Projektphase des Deutschen Textarchivs wurden diese Richtlinien noch nicht vollständig umgesetzt.


---

## Weitere Sonderzeichen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trApostrophe.html](https://www.deutschestextarchiv.de/doku/basisformat/trApostrophe.html)

# Weitere Sonderzeichen

Der Umgang mit Sonderzeichen, die nicht in der Unicode-Tabelle enthalten sind und somit
nicht kodiert werden können, wird im Kapitel [Schwer bzw. nicht entzifferbare Zeichen](gapSupplied.html)
des DTA-Basisformats näher erläutert.


---

## Diakritika

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trDiakritika.html](https://www.deutschestextarchiv.de/doku/basisformat/trDiakritika.html)

# Diakritika

Diakritika werden nach Möglichkeit mittels Unicode-Entitäten realisiert,
z. B. das hochgestellte o über u bzw. U
(U+0366, COMBINING LATIN SMALL LETTER O) , das c-Cedille
(ç, U+00E7, LATIN SMALL LETTER C WITH CEDILLA), die e caudata
(ę, U+0119, LATIN SMALL LETTER E WITH OGONEK) in der Bedeutung ae
oder das e mit Trema (ë, U+00EB, LATIN SMALL LETTER E WITH DIAERESIS).

Die Grundlage für die Transkription bildet der deutsche bzw. lateinische
Zeichensatz. Zeichen anderer Alphabete (Griechisch, Kyrillisch, Hebräisch etc.)
werden mittels ihrer entsprechenden Unicode-Entitäten realisiert. Gültig
ist der Unicode-Standard zum Zeitpunkt der Erfassung. Die Unicode-Listen, die
eine Vielzahl der Fälle abdecken, finden sich unter
<http://www.unicode.org/charts/>.

Die wichtigsten Listen im Überblick:

* [Lateinische Buchstaben Standard (Controls and Basic Latin)](http://www.unicode.org/charts/PDF/U0000.pdf)
* [Ergänzungen zum lateinischen Zeichensatz (Controls and Latin-1 Supplement)](http://www.unicode.org/charts/PDF/U0080.pdf)
* [griechischer Zeichensatz (Greek and Coptic)](http://www.unicode.org/charts/PDF/U0370.pdf)
* [erweiterter griechischer Zeichensatz (Greek extended)](http://www.unicode.org/charts/PDF/U1F00.pdf)
* [kyrillischer Zeichensatz (Cyrillic)](http://www.unicode.org/charts/PDF/U0400.pdf)
* [Kombinierte diakritische Zeichen (Combining diacritical marks)](http://www.unicode.org/charts/PDF/U0300.pdf)


---

## Definitionen und Konventionen für diese Richtlinien

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trDokuKonventionen.html](https://www.deutschestextarchiv.de/doku/basisformat/trDokuKonventionen.html)

# Definitionen und Konventionen für diese Richtlinien

Unter der **Vorlage** sind, so nicht anders vermerkt, die digitalen
Faksimiles einer Buchausgabe zu verstehen, auf welchen der DTA-Volltext
basiert.

Nichtproportionalschrift wird verwendet für:

* die Angabe von Textbeispielen
* die Angabe von Tags bzw. Codebeispielen

Die Notation `U+NNNN` verweist auf ein entsprechendes Unicode-Zeichen.
Desweiteren wird in den Transkriptionsbeispielen bei höherbittigen Unicode-Zeichen
die von XML abgeleitete Notationsform `&#xNNNN;` benutzt.


---

## Gedankenstrich

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trGedankenstrich.html](https://www.deutschestextarchiv.de/doku/basisformat/trGedankenstrich.html)

# Gedankenstrich

Gedankenstriche können in verschiedenen Längen auftreten. Soweit sie in
dieser Verschiedenheit erkannt werden, werden sie als folgende hexadezimale
Unicode-Entitäten wiedergegeben:

| Zeichen | Entität | Beschreibung |
| --- | --- | --- |
| `-` | `U+002D` | Bindestrich/Silbentrennstrich/Minuszeichen (`HYPHEN-MINUS`) |
| `‒` | `U+2012` | Ziffernstrich (`FIGURE DASH`) |
| `–` | `U+2013` | Halbgeviertstrich (Gedankenstrich) (`EN DASH`) |
| `—` | `U+2014` | Geviertstrich (langer Gedankenstrich) (`EM DASH`) |

Ist eine Unterscheidung der Länge des Gedankenstriches nicht erkennbar, wird
dieser als Halbgeviertstrich erfasst.


---

## Grundsätzliches zur Transkription

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trGrundsaetze.html](https://www.deutschestextarchiv.de/doku/basisformat/trGrundsaetze.html)

# Grundsätzliches zur Transkription

Die Texterfassung erfolgt grundsätzlich vorlagengetreu im Unicode-Format
(Kodierung in UTF-8) des zum Zeitpunkt der Erfassung gültigen
Unicode-Standards. Dabei werden die Zeichen, wenn möglich,
hinsichtlich ihrer Semantik abgebildet.

Auf modernisierende Veränderungen des lexikalischen Materials wird in der
Regel verzichtet, z. B. auch in Bezug auf die Schreibung von
Eigennamen. Auch Druckfehler werden übernommen (zum Verfahren der
Druckfehlerannotation siehe das entsprechende [Kapitel im DTA-Basisformat](eeDruckfehler.html)).

Zur Behandlung von unleserlichen bzw. schwer entzifferbaren Zeichen siehe das
entsprechende [Kapitel im
DTA-Basisformat](gapSupplied.html).

Ausnahmen und Abweichungen davon werden ausführlich in diesem Dokument
besprochen.


---

## Ligaturen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trLigatur.html](https://www.deutschestextarchiv.de/doku/basisformat/trLigatur.html)

# Ligaturen

Vokalische Ligaturen werden grundsätzlich realisiert:

| Vorlage | Zeichen | Entität | Beschreibung |
| --- | --- | --- | --- |
| ae-Ligatur | `æ` | `U+00E6` | `LATIN SMALL LETTER AE` |
| oe-Ligatur | `œ` | `U+0153` | `LATIN SMALL LIGATURE OE` |

Konsonantische Ligaturen (`tz`, `ct`, `ts`, `ff` etc.)
sowie die Ligatur `ij` werden dagegen grundsätzlich aufgespalten.


---

## Abbreviaturen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trNasalstrich.html](https://www.deutschestextarchiv.de/doku/basisformat/trNasalstrich.html)

# Abbreviaturen

## Horizontale Kürzungsstriche

Horizontale Kürzungsstriche (Balken oder geschlängelte Linie über Buchstaben als Substituenten für ausgelassene Zeichen, Nasalstrich) werden mittels des Zeichens U+0303, COMBINING TILDE transkribiert.

| Vorlage | Transkription |
| --- | --- |
|  | `from&#x0303;en` |
|  | `Un&#x0303; macht` |

## Vertikale Kürzungsstriche

Vertikale Kürzungsstriche werden in der Regel mit dem Unicode-Zeichen U+0315, COMBINING COMMA ABOVE RIGHT wiedergegeben

| Vorlage | Transkription |
| --- | --- |
|  | `Daher d̕ Pre-` |
|  | `darund̕` iſt |

Tipp:

Zur Expansion von Abkürzungen s. Kapitel [Auflösung von Abkürzungen](abkuerzung.html).


---

## Reservierte Zeichen bei der Strukturierung der Transkription mit XML

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trReservierteZeichen.html](https://www.deutschestextarchiv.de/doku/basisformat/trReservierteZeichen.html)

# Reservierte Zeichen bei der Strukturierung der Transkription mit XML

Da eine Transkription in einem XML-Format empfohlen wird, muss darauf geachtet werden, dass
**spitze Klammern** im Transkriptionstext mit `&lt;` (<) und
`&gt;` (>) wiedergegeben werden.

Das sog. **„Kaufmanns-Und“/„Ampersand“** (&) wird entsprechend als `&amp;` realisiert.


---

## Unterscheidung von I vs. J

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungIJ.html](https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungIJ.html)

# Unterscheidung von I vs. J

Der Typensatz der Frakturschrift weist in der Regel nur ein Graphem für die
heutigen Majuskeln I und J auf. In der Transkription wird
dieses Graphem nicht entsprechend des Lautwerts jeweils als I- bzw.
J-Graphem wiedergegeben, sondern es steht grundsätzlich die Majuskel
J.

Im Falle von Abkürzungen steht ebenfalls grundsätzlich die Majuskel J
(z. B. J. E. Hitzig bei Julius/Iulius Eduard Hitzig
und K. J. Beck für Karl Isidor/Jsidor Beck).


---

## r-Grapheme

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungR.html](https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungR.html)

# r-Grapheme

Für das sog. runde r steht die Unicode-Entität ꝛ (U+A75B, LATIN SMALL LETTER R ROTUNDA). Es findet sich
häufig in Zusammenhang mit dem heute gebräuchlichen r oder als et-Substituent
in Abkürzungen für et cetera.

Beispiel (rundes r als heutiges r und als et):

| Vorlage | Transkription |
| --- | --- |
| Herr (mit rundem r) | `Her&#xA75B;` |
| etc. (mit rundem r) | `&#xA75B;c.` |


---

## s-Grapheme

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungS.html](https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungS.html)

# s-Grapheme

Sowohl in Fraktur- als auch in Antiquatexten können zwei Formen des
Kleinbuchstabens s auftreten: das Schaft-s (ſ, U+017F, LATIN SMALL LETTER LONG S)
und das runde s (s, U+0073, LATIN SMALL LETTER S). Sie werden in der Transkription unterschieden.

Die ursprüngliche zusammengesetzte Form aus Schaft-s + s wird beibehalten:
`&#x017F;s`.

Die Ligatur Schaft-s + z wird als ß wiedergegeben.


---

## Unterscheidung von u und v

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungUV.html](https://www.deutschestextarchiv.de/doku/basisformat/trSchreibungUV.html)

# Unterscheidung von u und v

Die Grapheme u und v, die in den Vorlagen jeweils sowohl den
Laut /u/ als auch den Laut /f/ repräsentieren können, werden vorlagengetreu
wiedergegeben.
(z. B. vnd, vnuertig).


---

## Schreibweisen, spezielle Zeichen und Sonderzeichen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSchreibweisen.html](https://www.deutschestextarchiv.de/doku/basisformat/trSchreibweisen.html)

# Schreibweisen, spezielle Zeichen und Sonderzeichen

* [Unterscheidung von I vs. J](trSchreibungIJ.html)
* [Unterscheidung von u und v](trSchreibungUV.html)
* [s-Grapheme](trSchreibungS.html)
* [r-Grapheme](trSchreibungR.html)
* [Ligaturen](trLigatur.html)
* [Umlaute](trUmlaute.html)
* [Abbreviaturen](trNasalstrich.html)
* [Diakritika](trDiakritika.html)
* [Reservierte Zeichen](trReservierteZeichen.html)
* [Weitere Sonderzeichen](trApostrophe.html)
* [Silbentrennung](trSilbentrennung.html)


---

## Silbentrennung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSilbentrennung.html](https://www.deutschestextarchiv.de/doku/basisformat/trSilbentrennung.html)

# Silbentrennung

Als Silbentrennstrich wird, ungeachtet des Erscheinungsbildes im Text, der
Bindestrich (`U+002D`) verwendet.

In Texten, die durch OCR (Optical Character Recognition) erfasst
wurden, kann als Silbentrennstrich `¬` (`U+00AC`) stehen.


---

## Zahlen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trSonderzeichen.html](https://www.deutschestextarchiv.de/doku/basisformat/trSonderzeichen.html)

# Zahlen

Sind große **Zahlen in Blöcken** gedruckt, werden keine Leerzeichen innerhalb des
Zahlenblocks gesetzt, z. B. `1000000` (es wird also von der Vorlage abgewichen).

Bei **Prozentangaben** steht: Zahl Leerzeichen %-Zeichen; z. B. `50 %`.

Bei **Temperaturangaben** steht vor der Einheit ein Leerzeichen; z. B. `360 °C`.

**Brüche:** Brüche werden, sofern vorhanden, mittels ihrer entsprechenden
Unicode-Entitäten wiedergegeben:

| Zeichen | Entität |
| --- | --- |
| ½ | `U+00BD` |
| ⅓ | `U+2153` |
| ⅔ | `U+2154` |
| ¼ | `U+00BC` |
| ¾ | `U+00BE` |
| ⅕ | `U+2155` |
| ⅖ | `U+2156` |
| ⅗ | `U+2157` |
| ⅘ | `U+2158` |
| ⅙ | `U+2159` |
| ⅚ | `U+215A` |
| ⅐ | `U+2150` |
| ⅛ | `U+215B` |
| ⅜ | `U+215C` |
| ⅝ | `U+215D` |
| ⅞ | `U+215E` |
| ⅑ | `U+2151` |
| ⅒ | `U+2152` |

Alle sonstigen Brüche können mithilfe des DTA-Basisformats als Formel
transkribiert werden (siehe
[DTA-Basisformat, Kapitel: Formeln](formelnAllg.html)).

Für mathematische oder physikalische Konstanten gelten die folgenden
Unicode-Zeichensätze:

* [Math alphanumeric Symbols](http://www.unicode.org/charts/PDF/U1D400.pdf)
* [Number Forms](http://www.unicode.org/charts/PDF/U2150.pdf)


---

## Umlaute

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trUmlaute.html](https://www.deutschestextarchiv.de/doku/basisformat/trUmlaute.html)

# Umlaute

Umlaute werden entsprechend der Vorlage transkribiert, d. h. die Umlaute in
den heute gebräuchlichen Formen Ä, Ö, Ü, ä,
ö, ü werden von solchen, die durch ein hochgestelltes e
(U+0364, COMBINING LATIN SMALL LETTER E) über Vokal gekennzeichnet sind,
unterschieden (z. B. `u&#x0364;`).


---

## Zeichensetzung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trZeichensetzung.html](https://www.deutschestextarchiv.de/doku/basisformat/trZeichensetzung.html)

# Zeichensetzung

## Themen

* [Zeichensetzung Grundregeln](trZeichensetzungAllg.html)
* [Gedankenstrich](trGedankenstrich.html)
* [Anführungszeichen](trAnfZeichen.html)


---

## Grundregeln zur Zeichensetzung

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/trZeichensetzungAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/trZeichensetzungAllg.html)

# Grundregeln zur Zeichensetzung

Alle Satzzeichen (Fragezeichen, Ausrufezeichen, Punkt, Komma, Semikolon,
Doppelpunkt, Virgel) werden wie gedruckt erfasst. Auf eine Normalisierung der
Zeichensetzung nach heutigen Standards wird verzichtet.

Satzzeichen stehen ohne Leerzeichen direkt am vorangehenden Wort. Im
Anschluss folgt ein Leerzeichen. Anführungszeichen und Klammerungen stehen
ohne Leerzeichen direkt an dem durch sie eingeschlossenen Text. Ebenso
schmiegen sich Fußnotenreferenzen ohne Leerraum direkt an das vorangehende
Zeichen an.

Der Abdruck, den ein beim Druckvorgang heruntergefallenes Spatium auf der Seite
hinterlässt, wird nicht mit transkribiert.

Mehrere Punkte hintereinander, die eine Auslassung verdeutlichen sollen,
werden von jeweils einem Leerzeichen umschlossen. Eine Ausnahme bilden
Punkte, die einen Wortabbruch verdeutlichen. Sie stehen ohne Leerzeichen
direkt hinter dem unvollständigen Wort.

Vor und nach Gedankenstrichen mitten im Satz steht jeweils ein Leerzeichen.
Steht der Gedankenstrich direkt vor einem Satzzeichen, wird dazwischen kein
Leerzeichen getippt.

Für die Zeichensetzung gilt die Unicode-Tabelle [General Punctuation](http://www.unicode.org/charts/PDF/U2000.pdf).


---

## Richtlinien zur Transkription

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/transkription.html](https://www.deutschestextarchiv.de/doku/basisformat/transkription.html)

# Richtlinien zur Transkription

Richtlinien zur Erfassung der Volltexte

Ziel des Deutschen Textarchivs (DTA) ist die Erstellung eines
disziplinenübergreifenden Volltextkorpus deutschsprachiger Texte.
Grundlage hierfür bilden digitale Faksimiles historischer Druckwerke
(Entstehungszeit der Drucke zwischen ca. 1650 und 1900). Das Korpus
umfasst Werke verschiedener Textsorten, literarischer Gattungen und
wissenschaftlicher Disziplinen. Ziel des Projekts ist die
Bereitstellung und – aufgrund der großen Textmenge weitestgehend
automatische – linguistische Aufbereitung eines vielseitigen,
umfangreichen Textbestandes auf dieser heterogenen Grundlage.

Die Erfassung der Texte im DTA erfolgt nach dem Prinzip der Wahrung des
historischen Sprachstandes der Texte. Aufgrund dieser Zielsetzung
wird darauf geachtet, bei der Texterfassung die Zahl der
(unvermeidbaren) Interpretationen typographischer Gegebenheiten
gering zu halten. Um unbewusste Modernisierungen oder Korrekturen zu
vermeiden, werden die Texte von Nicht-Muttersprachlern eingegeben
(siehe dazu auch [Volltextdigitalisierung im Deutschen
Textarchiv](http://www.deutschestextarchiv.de/doku/workflow#Die_Volltextdigitalisierung)). Eine Druckfehlerkorrektur erfolgt daher während
der Erfassung nicht, kann aber im Erschließungs- und
Korrekturprozess eingeschränkt vorgenommen werden.

Aus dem Prinzip größtmöglicher Bewahrung des Vorlagentextes bei
gleichzeitiger Konzentration auf die lexikalischen Gegebenheiten
ergeben sich für die Texterfassung die folgenden Richtlinien.


---

## Richtlinien zur Kodierung typographischer Besonderheiten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/typogrAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/typogrAllg.html)

# Richtlinien zur Kodierung typographischer Besonderheiten

In den Vorlagen wird die semantische Struktur einer Passage in der Regel durch
typographische Hervorhebungen verdeutlicht. Die Annotation des Volltextes folgt in erster
Linie semantischen Kriterien, so dass dem transkribierten Text jeweils die betreffende
semantische Kategorie zugeordnet wird.

Das typographische Erscheinungsbild der Vorlage wird daneben ebenfalls
möglichst genau dokumentiert, insbesondere aber dann, wenn die semantische Struktur einer
Passage nicht auf den ersten Blick erkennbar ist.

Typographische Besonderheiten der Vorlage werden mittels der
Universalattribute `@rendition` und `@rend` wiedergegeben,
welche folgenden Elementen des Basisformats zugeordnet werden können:
`<byline>, <cell>, <dateline>, <div>,
<figure>, <floatingText>, <formula>, <fw>, <head>, <hi>,
<l>, <lg>, <milestone>, <p>`

HINWEIS:

***Abweichende Regelung Phase 1:** Für die Auszeichnung typographischer Besonderheiten wird das Element
`<hi>` eingesetzt, welches das Attribut `@rendition`
enthält.*

Das Element `<hi>` wird speziell für die
Auszeichnung typographischer Besonderheiten auf Zeichenebene eingesetzt.

Typographische Auszeichnungen können über einen Seiten- bzw. Spaltenumbruch hinwegreichen.

Die Attribute `@rendition` und `@rend` schließen einander
aus. Das Attribut `@rendition` enthält eine feste Liste möglicher Werte für
die Auszeichnung gängiger typographischer Besonderheiten (s. unten) und sollte daher dem
Attribut `@rend` vorgezogen werden. Darüber hinaus gehende typographische
Besonderheiten, die sich nicht mit den unten genannten Werten abbilden lassen, können im
Attribut `@rend` wiedergegeben werden. In `@rend` sind
natürlichsprachliche Angaben zur typographischen Realisierung der jeweils ausgezeichneten
Textpassagen möglich.

Folgende Werte kann `@rendition` annehmen:

| Attribut-Wert-Paar | Bedeutung | CSS-Umsetzung im DTA |
| --- | --- | --- |
| `rendition="#aq"` | Wechsel zur Antiqua-Schrift in Fraktur-Werken | `font-family:sans-serif` |
| `rendition="#b"` | Fettdruck | `font-weight:bold` |
| `rendition="#blue"` | blaue Schrift | `color:blue` |
| `rendition="#c"` | zentrierter Text | `display:block; text-align:center` |
| `rendition="#et"` | eingerückter Text | `display:block; margin-left:2em; text-indent:0` |
| `rendition="#f"` | Wechsel zur Frakturschrift in Antiqua-Werken | `border:1px dotted silver` |
| `rendition="#fr"` | Frakturwechsel | `border:1px dotted silver` |
| `rendition="#g"` | Sperrdruck | `letter-spacing:0.125em` |
| `rendition="#i"` | Kursivdruck | `font-style:italic` |
| `rendition="#in"` | Initiale, Schmuckinitiale | `font-size:150%` |
| `rendition="#k"` | Kapitälchen | `font-variant:small-caps` |
| `rendition="#red"` | roter Druck | `color:red` |
| `rendition="#right"` | Rechtsbündigkeit | `display:block; text-align:right` |
| `rendition="#sub"` | Tiefstellung | `vertical-align:sub; font-size:.7em` |
| `rendition="#sup"` | Hochstellung | `vertical-align:super; font-size:.7em` |
| `rendition="#u"` | gedruckte Unterstreichung | `text-decoration:underline` |
| `rendition="#uu"` | doppelte Unterstreichung | `border-bottom:double 3px #000` |
| `rendition="#v"` | vertikal gedruckter Text |  |
| `rendition="#s"` | durchgestrichener Text | `text-decoration:line-through` |
| `rendition="#et2"` | (Level 3:) zweifach eingerückter Text | `display:block; margin-left:4em; text-indent:0` |
| `rendition="#et3"` | (Level 3:) dreifach eingerückter Text | `display:block; margin-left:6em; text-indent:0` |
| `rendition="#smaller"` | (Level 3:) gegenüber dem Grundtext verkleinerte Schrift | `font-size:smaller` |
| `rendition="#larger"` | (Level 3:) gegenüber dem Grundtext vergrößerte Schrift | `font-size:larger` |


---

## Beispiele und Spezifika der Kodierung typographischer Besonderheiten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/typogrBspe.html](https://www.deutschestextarchiv.de/doku/basisformat/typogrBspe.html)

# Beispiele und Spezifika der Kodierung typographischer Besonderheiten

## Themen

* [Fettdruck](fettdruck.html)
* [Sperrdruck](sperrdruck.html)
* [Kapitälchen](kapitaelchen.html)
* [Initialen](initiale.html)
* [Übergeschriebenes](uebergeschrieben.html)
* [Einfärbungen](einfaerbung.html)
* [Tiefstellung](tiefstellung.html)
* [Hochstellung](hochstellung.html)
* [Eingerückter Text](einrueckung.html)
* [Typographie Satzzeichen](typogrSatzzeichen.html)
* [Schriftartwechsel](schriftart.html)


---

## Typographisches Erscheinungsbild der Satzzeichen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/typogrSatzzeichen.html](https://www.deutschestextarchiv.de/doku/basisformat/typogrSatzzeichen.html)

# Typographisches Erscheinungsbild der Satzzeichen

Satzzeichen werden in Bezug auf ihr typographisches Erscheinungsbild (Fettdruck,
Sperrung etc.) nach Möglichkeit vorlagengetreu wiedergegeben. Geht die Formatierung
eines Satzzeichens nicht sicher aus der Vorlage hervor, wird es außerhalb des
Einflussbereichs des `@rendition`-Attributs gesetzt.


---

## Typographische Besonderheiten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/typographie.html](https://www.deutschestextarchiv.de/doku/basisformat/typographie.html)

# Typographische Besonderheiten

## Themen

* [Richtlinien der Kodierung](typogrAllg.html)
* [Beispiele und Spezifika der Kodierung](typogrBspe.html)


---

## Übergeschriebenes

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/uebergeschrieben.html](https://www.deutschestextarchiv.de/doku/basisformat/uebergeschrieben.html)

# Übergeschriebenes

Kombinationen aus Zeichen mit übergeschriebenen Zeichen, für die es keine
Unicode-Entsprechung gibt, werden mittels `<hi @rendition="#stacked">`
ausgezeichnet. Die betreffenden Zeichen werden entsprechend der Unicode-Empfehlung für die
[Schreibung
von Binomialkoeffizienten](http://unicode.org/notes/tn28/UTN28-PlainTextMath-v2.pdf) mittels einer unterbrochenen Pipe (¦ U+00A6 BROKEN BAR)
voneinander getrennt. Dabei steht das Basiszeichen jeweils an erster Stelle.

## Übergeschriebene Zeichen

![](img/rh21LavgZb.png)

```
0,28 <hi rendition="#stacked">P&#x0336; ￤ ˙˙˙ ￤ ˙˙</hi>
```

*Quelle: [Quenstedt, Friedrich August: Handbuch der
Mineralogie. Tübingen, 1855. [Faksimile 510]](http://www.deutschestextarchiv.de/quenstedt_mineralogie_1854/510)*

Folgen mehrere übergeschriebene Zeichen übereinander, so wird `<hi rendition="#stacked">`
geschachtelt.

## Mehrfach übereinander geschriebene Zeichen

![](img/bachUebergeschr.png)

```
<hi rendition="#stacked">2 ￤ 4</hi>
und
<hi rendition="#stacked">2 ￤ 4 ￤ 6</hi>
```

*Quelle: [Bach, Carl Philipp Emanuel: Versuch über die wahre Art das Clavier zu spielen. Bd. 2. Berlin, 1762. [Faksimile 107]](http://www.deutschestextarchiv.de/bach_versuch02_1762/107)*


---

## Übersicht über die Elemente im Header-Bereich

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/uebersichtHeader.html](https://www.deutschestextarchiv.de/doku/basisformat/uebersichtHeader.html)

# Übersicht über die Elemente im Header-Bereich

Die folgende Tabelle bietet einen Überblick über alle Elemente, die das DTA-Basisformat für den
`<teiHeader>`-Bereich vorsieht. Jedem Element sind die jeweils laut
DTA-Basisformat möglichen Attribute und (falls invariabel) Werte zugeordnet. Den Elementen
sind funktionale Kategorien zugeordnet, welche über deren Verwendungskontexte informieren.
Beschreibungen zu diesen funktionalen Kategorien finden sich in der
[Legende zu den Übersichten](legende.html#legende__hb-fk).
Die Attribute des DTA-Basisformats, die in den meisten der DTA-Elemente verwendet werden können
(Universalattribute), sind ebenfalls in der
[Legende zu den Übersichten](legende.html#legende__hb-ga) dokumentiert.

| Element | Beschreibung | Attribute/Anmerkungen | | Funktionale Kategorie |
| --- | --- | --- | --- | --- |
| `addName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-addName.html), [DTABf](mdPersName.html) | zusätzlicher Name, z.B. Pseudonym |  | | [names](legende.html#legende__fkh04) |
| `address` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-address.html), [DTABf](mdPubStmtAllg.html) | Adresse |  | | [publication](legende.html#legende__fkh05) |
| `addrLine` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-addrLine.html), [DTABf](mdPubStmtAllg.html) | Postanschrift |  | | [publication](legende.html#legende__fkh05) |
| `author` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-author.html), [DTABf](mdAuthorEditor.html) | Autor |  | | [authorTitle](legende.html#legende__fkh02) |
| `availability` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-availability.html), [DTABf](mdLicense.html) | Angaben zur Nachnutzbarkeit | `@corresp` | ID des korrespondierenden [`availability`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-availability.html)- oder [`msDesc`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-msDesc.html)-Elements | [publication](legende.html#legende__fkh05) |
| `@xml:id` | eindeutige ID |
| `bibl` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-bibl.html), [DTABf](mdSdBibl.html) | Zitiertitel | `@type` | [`"DM"`, `"DS"`, `"J"`, `"JA"`, `"M"`, `"MAN"`, `"MM"`, `"MMS"`, `"MS"`] | [authorTitle](legende.html#legende__fkh02) |
| `biblFull` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-biblFull.html), [DTABf](mdSdBiblFull.html) | ausführliche Titelangaben |  | | [authorTitle](legende.html#legende__fkh02) |
| `biblScope` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-biblScope.html), [DTABf](mdSdSeriesStmt.html) | Position des Textes innerhalb einer übergeordneten Publikation | `@unit` | Kontext der Einordnung [`"issue"`, `"pages"`, `"volume"`] | [sources](legende.html#legende__fkh07) |
| `classCode` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-classCode.html), [DTABf](mdProfileDesc.html) | Textsorte | `@scheme` | Klassifikationsschema (URL) | [classification](legende.html#legende__fkh03) |
| `date` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-date.html), [DTABf](mdSdPublicationStmt.html), [DTABf2](mdPubStmtAllg.html) | Erscheinungsdatum/Datum des Zugriffs auf externe Ressource | `@type` | [`"creation"`, `"firstPublication"`, `"importDTA"`, `"publication"`] | [publication](legende.html#legende__fkh05), [responsibility](legende.html#legende__fkh06) |
| `edition` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-edition.html), [DTABf](mdEditionStmt.html) | Art der Edition | `@n` | Nummer der Auflage normiert (Ziffer) | [publication](legende.html#legende__fkh05) |
| `editionStmt` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-editionStmt.html), [DTABf](mdEditionStmt.html) | Angaben zur Edition |  | | [publication](legende.html#legende__fkh05) |
| `editor` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-editor.html), [DTABf](mdAuthorEditor.html) | Editor/Herausgeber | `@corresp` | ID des korrespondierenden [`publisher`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-publisher.html)-Elements. | [authorTitle](legende.html#legende__fkh02), [responsibility](legende.html#legende__fkh06) |
| `@role` | Übersetzer [`"translator"`] |
| `editorialDecl` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-editorialDecl.html), [DTABf](mdEncodingDesc.html) | Angaben zu den Transkriptions- und Annotationsrichtlinien |  | | [appearance](legende.html#legende__fkh01) |
| `email` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-email.html), [DTABf](mdPubStmtAllg.html) | E-Mail-Adresse |  | | [publication](legende.html#legende__fkh05) |
| `encodingDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-encodingDesc.html), [DTABf](mdEncodingDesc.html) | Hinweise zu den Transkriptions- und Annotationsrichtlinien |  | | [appearance](legende.html#legende__fkh01) |
| `extent` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-extent.html), [DTABf](mdExtent.html) | Umfang des Volltextes/der Quelle |  | | [appearance](legende.html#legende__fkh01) |
| `fileDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-fileDesc.html), [DTABf](mdBiblAngaben.html) | ausführliche bibliographische Angaben |  | | [authorTitle](legende.html#legende__fkh02) |
| `forename` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-forename.html), [DTABf](mdPersName.html) | Vorname |  | | [names](legende.html#legende__fkh04) |
| `genName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-genName.html), [DTABf](mdPersName.html) | Generationenangabe |  | | [names](legende.html#legende__fkh04) |
| `idno` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-idno.html), [DTABf](mdPubStmtAllg.html) | Identifikationscode | `@type` | Art der ID [`"DTADirName"`, `"DTAID"`, `"shelfmark"`, `"URLCAB"`, `"URLCatalogue"`, `"URLHTML"`, `"URLImages"`, `"URLTCF"`, `"URLText"`, `"URLWeb"`, `"URLXML"`, `"URN"`] | [sources](legende.html#legende__fkh07), [publication](legende.html#legende__fkh05) |
| `language` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-language.html), [DTABf](mdProfileDesc.html) | Sprache | `@ident` | Sprachcode nach ISO 639-3 | [appearance](legende.html#legende__fkh01) |
| `langUsage` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-langUsage.html), [DTABf](mdProfileDesc.html) | Angaben zur Sprache des Textes |  | | [appearance](legende.html#legende__fkh01) |
| `licence` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-licence.html), [DTABf](mdLicense.html) | Lizenz | `@target` | Verweis zu Informationen zur Lizenz (URL) | [publication](legende.html#legende__fkh05) |
| `measure` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-measure.html), [DTABf](mdExtent.html) | Umfangsangabe | `@type` | Maßeinheiten [`"characters"`, `"images"`, `"pages"`, `"tokens"`, `"types"`] | [appearance](legende.html#legende__fkh01) |
| `msDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-msDesc.html), [DTABf](mdSdMsDesc.html) | Angaben zum zugrundeliegenden Druck | `@corresp` | ID des korrespondierenden [`availability`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-availability.html)-Elements | [sources](legende.html#legende__fkh07) |
| `@xml:id` | eindeutige ID |
| `msIdentifier` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-msIdentifier.html), [DTABf](mdSdMsDesc.html) | Angaben zum Aufbewahrungsort |  | | [sources](legende.html#legende__fkh07) |
| `name` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-name.html), [DTABf](mdSdPublicationStmt.html) | Name des Verlages/der Druckerei |  | | [names](legende.html#legende__fkh04) |
| `nameLink` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-nameLink.html), [DTABf](mdPersName.html) | Adelstitel |  | | [names](legende.html#legende__fkh04) |
| `note` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-note.html), [DTABf](mdNotesStmt.html), [DTABf2](mdSdNotesStmt.html), [DTABf3](mdRespStmt.html) | Anmerkung zur Verantwortlichkeit | `@type` | [`"remarkDocument"`, `"remarkResponsibility"`, `"remarkRevisionDTA"`, `"remarkSource"`] | [responsibility](legende.html#legende__fkh06) |
| `orgName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-orgName.html), [DTABf](mdPubStmtAllg.html), [DTABf2](mdRespStmt.html) | Name einer Organisation | `@ref` | Referenz zu weiteren Informationen zu der Organisation (URL) | [names](legende.html#legende__fkh04) |
| `p` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-p.html), [DTABf](mdLicense.html), [DTABf2](mdSdMsDesc.html), [DTABf3](mdEncodingDesc.html) | Paragraph |  | | [text](legende.html#legende__fkh08) |
| `persName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-persName.html), [DTABf](mdPersName.html) | Name einer Person (Autor, Herausgeber/Editor, Übersetzer, anderweitig verantwortliche Person) | `@ref` | Referenz zu weiteren Informationen zu der Person (URL) | [names](legende.html#legende__fkh04) |
| `physDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-physDesc.html), [DTABf](mdSdMsDesc.html) | Erscheinungsbild der Textvorlage |  | | [appearance](legende.html#legende__fkh01) |
| `profileDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-profileDesc.html), [DTABf](mdProfileDesc.html) | Einordnung des Textes |  | | [classification](legende.html#legende__fkh03) |
| `publicationStmt` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-publicationStmt.html), [DTABf](mdSdPublicationStmt.html), [DTABf2](mdPubStmtAllg.html) | Gegebenheiten der Publikation |  | | [publication](legende.html#legende__fkh05) |
| `publisher` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-publisher.html), [DTABf](mdSdPublicationStmt.html), [DTABf2](mdPubStmtAllg.html) | Verlag/Druckerei/Herausgeber der Publikation | `@xml:id` | eindeutige ID | [publication](legende.html#legende__fkh05) |
| `pubPlace` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-pubPlace.html), [DTABf](mdSdPublicationStmt.html), [DTABf2](mdPubStmtAllg.html) | Erscheinungsort |  | | [publication](legende.html#legende__fkh05) |
| `ref` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-ref.html), [DTABf](mdRespStmt.html) | Verweis auf eine externe (Text-/Bild-)Ressource | `@target` | Verweisziel (URL) | [responsibility](legende.html#legende__fkh06) |
| `repository` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-repository.html), [DTABf](mdSdMsDesc.html) | besitzende Bibliothek |  | | [sources](legende.html#legende__fkh07) |
| `resp` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-resp.html), [DTABf](mdRespStmt.html) | Art der Verantwortlichkeit |  | | [responsibility](legende.html#legende__fkh06) |
| `respStmt` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-respStmt.html), [DTABf](mdRespStmt.html) | Angaben zu Verantwortlichkeiten | `@corresp` | ID des korrespondierenden [`availability`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-availability.html)-Elements | [responsibility](legende.html#legende__fkh06) |
| `@xml:id` | eindeutige ID |
| `roleName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-roleName.html), [DTABf](mdPersName.html) | Funktion, welche die genannte Person ausübt(e) |  | | [names](legende.html#legende__fkh04) |
| `seriesStmt` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-seriesStmt.html), [DTABf](mdSdSeriesStmt.html) | Angaben zur übergeordneten Reihe/Zeitschrift |  | | [publication](legende.html#legende__fkh05) |
| `sourceDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-sourceDesc.html), [DTABf](mdSourceDesc.html) | Angaben zur zugrundeliegenden Quelle |  | | [sources](legende.html#legende__fkh07) |
| `surname` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-surname.html), [DTABf](mdPersName.html) | Nachname |  | | [names](legende.html#legende__fkh04) |
| `textClass` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-textClass.html), [DTABf](mdProfileDesc.html) | inhaltliche Einordnung des Textes |  | | [classification](legende.html#legende__fkh03) |
| `title` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-title.html), [DTABf](mdTitleStmt.html), [DTABf2](mdSdTitleStmt.html), [DTABf3](mdSdSeriesStmt.html) | Titelangabe(n) | `@level` | Art der Publikation (Monographie, Zeitungsartikel, ...) [`"a"`, `"j"`, `"m"`, `"s"`] | [authorTitle](legende.html#legende__fkh02) |
| `@n` | Nummer des Bandes/Teils |
| `@type` | Skopus des Titels (Haupttitel, Bandtitel, ...) [`"main"`, `"part"`, `"sub"`, `"volume"`] |
| `titleStmt` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-titleStmt.html), [DTABf](mdTitleStmt.html), [DTABf2](mdSdTitleStmt.html) | bibliographische Angaben (Titel, Verantwortlichkeiten) |  | | [authorTitle](legende.html#legende__fkh02) |
| `typeDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-typeDesc.html), [DTABf](mdSdMsDesc.html) | Schriftart |  | | [appearance](legende.html#legende__fkh01) |


---

## Übersicht über die Elemente im Textbereich

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/uebersichtText.html](https://www.deutschestextarchiv.de/doku/basisformat/uebersichtText.html)

# Übersicht über die Elemente im Textbereich

Die folgende Tabelle bietet einen Überblick über alle Elemente, die das DTA-Basisformat für den
`<text>`-Bereich vorsieht. Jedem Element sind die jeweils laut DTA-Basisformat
möglichen Attribute und (falls invariabel) Werte zugeordnet. Jedem Element ist ein Level zugeordnet,
welches dessen Verwendungsstatus im DTA-Kernkorpus spezifiziert. Den Elementen sind weiterhin
funktionale Kategorien zugeordnet, welche über deren Verwendungskontexte informieren. Die Attribute
des DTA-Basisformats, die in den meisten der DTA-Elemente verwendet werden können (Universalattribute),
sind in der [Legende zu den Übersichten](legende.html#legende__tb-ga) dokumentiert.
Dort findet sich ebenso eine nähere Dokumentation der [Levels](legende.html#legende__tb-tl)
und der [funktionalen Kategorien](legende.html#legende__tb-fk).

| Element | Beschreibung | Attribute/Anmerkungen | | Funktionale Kategorie | Level |
| --- | --- | --- | --- | --- | --- |
| `ab` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-ab.html) | Anonymer Block/Container | *stattdessen  [`div`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div.html) ,  [`floatingText`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-floatingText.html) oder  [`p`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-p.html)  benutzen* | | [textStructure](legende.html#legende__fk09) | [4 (unzulässig)](legende.html#legende__l04) |
| `abbr` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-abbr.html), [DTABf](abkuerzung.html) | Abkürzung |  | | [phraseStructure](legende.html#legende__fk07), [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `actor` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-actor.html), [DTABf](drFiguren.html) | Name eines Schauspielers innerhalb einer Darstellerliste |  | | [drama](legende.html#legende__fk03), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `add` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-add.html), [DTABf](msAddDel.html) | Hinzufügung durch den Autor | nur in Manuskripten zu verwenden | | [manuscripts](legende.html#legende__fk12), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `argument` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-argument.html), [DTABf](teaser.html) | Inhaltszusammenfassung |  | | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `back` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-back.html), [DTABf](TEIStruktur.html), [DTABf2](anhAllg.html) | Anhang |  | | [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `bibl` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-bibl.html), [DTABf](bibliographie.html), [DTABf2](zitateEpigraphe.html) | bibliographische Angabe |  | | [citations](legende.html#legende__fk01), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `body` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-body.html) [DTABf](TEIStruktur.html), [DTABf2](bodyAllg.html) | Textkörper |  | | [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `byline` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-byline.html) [DTABf](tbAllg.html) | Angabe zur Urheberschaft |  | | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `c` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-c.html) | ein Zeichen | *wird im DTA-Korpus standoff annotiert* | | [phraseStructure](legende.html#legende__fk07) | [4 (unzulässig)](legende.html#legende__l04) |
| `castGroup` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-castGroup.html) [DTABf](drFiguren.html) | Gruppe von Personen (Drama) |  | | [drama](legende.html#legende__fk03), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `castItem` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-castItem.html) [DTABf](drFiguren.html) | Beschreibung einer Rolle (Drama) |  | | [drama](legende.html#legende__fk03), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `castList` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-castList.html) [DTABf](drFiguren.html) | Liste der handelnden Personen (Drama) |  | | [drama](legende.html#legende__fk03), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `cb` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-cb.html), [DTABf](spalte.html) | Spaltenumbruch | `@n` | Spaltennummer | [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `@type` | [`"end"`, `"start"`] |
| `cell` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-cell.html), [DTABf](tabAllg.html) | Tabellenzelle | `@cols` | Spaltenumfang | [tables](legende.html#legende__fk08) | [1 (notwendig)](legende.html#legende__l01) |
| `@role` | Funktion des Zelleninhalts für die Tabelle [`"label"`] |
| `@rows` | Zeilenumfang |
| `choice` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-choice.html), [DTABf](eeAllg.html) | Auswahl bei Änderungen gegenüber der Vorlage (Transkription/Encoding) |  | | [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `cit` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-cit.html), [DTABf](zitateEpigraphe.html) | Zitat |  | | [citations](legende.html#legende__fk01), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `closer` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-closer.html), [DTABf](brAllg.html) | beschließender Text (Brief) |  | | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `corr` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-corr.html), [DTABf](eeDruckfehler.html) | (bei Korrekturen:) korrigierte Form | `@resp` | Manuskripte: Person, die verantwortlich ist für die Ergänzung [`"[pointer]"`] | [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `@type` | Ursprung der Korrektur [`"addenda"`, `"corrigenda"`, `"editorial"`] |
| `date` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-date.html), [DTABf](datum.html) | Datumsangabe | `@when` | Datum in ISO-8601-Form | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `dateline` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-dateline.html), [DTABf](brAllg.html), [DTABf2](geLyrikband.html) | Abfassungsort und -zeit im Brief |  | | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `del` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-del.html), [DTABf](msAddDel.html) | Tilgung durch den Autor | nur in Manuskripten zu verwenden | | [manuscripts](legende.html#legende__fk12), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `div` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div.html), [DTABf](div.html) | Textabschnitt | `@n` | Strukturtiefe des Textabschnittes | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `@type` | Art des Textabschnittes [`"abbreviations"`, `"act"`, `"advertisement"`, `"appendix"`, `"bibliography"`, `"chapter"`, `"contents"`, `"copyright"`, `"corrigenda"`, `"dedication"`, `"diaryEntry"`, `"edition"`, `"figures"`, `"frontispiece"`, `"imprimatur"`, `"imprint"`, `"index"`, `"letter"`, `"lexiconEntry"`, `"poem"`, `"postface"`, `"preface"`, `"recipe"`, `"scene"`, `"session"`] |
| `div1` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div1.html), | Textabschnitt mit Strukturtiefe 1 | *stattdessen <div n="1"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div2` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div2.html), | Textabschnitt mit Strukturtiefe 2 | *stattdessen <div n="2"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div3` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div3.html) | Textabschnitt mit Strukturtiefe 3 | *stattdessen <div n="3"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div4` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div4.html) | Textabschnitt mit Strukturtiefe 4 | *stattdessen <div n="4"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div5` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div5.html) | Textabschnitt mit Strukturtiefe 5 | *stattdessen <div n="5"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div6` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div6.html) | Textabschnitt mit Strukturtiefe 6 | *stattdessen <div n="6"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `div7` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-div7.html) | Textabschnitt mit Strukturtiefe 7 | *stattdessen <div n="7"> benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `docAuthor` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-docAuthor.html), [DTABf](tbAllg.html) | Autor (Dokument) |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `docDate` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-docDate.html), [DTABf](tbAllg.html) | Erscheinungsjahr (Dokument) | `@when` | Datum in ISO-8601-Form | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `docEdition` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-docEdition.html), [DTABf](tbAllg.html) | Angaben zur Ausgabe (Dokument) |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `docImprint` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-docImprint.html), [DTABf](tbAllg.html) | Impressum (Dokument) |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `docTitle` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-docTitle.html), [DTABf](tbAllg.html) | Titel (Dokument) |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `epigraph` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-epigraph.html), [DTABf](epigraphe.html) | Epigraph |  | | [citations](legende.html#legende__fk01), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `expan` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-expan.html), [DTABf](abkuerzung.html) | Abkürzungsausschrift | `@resp` | Manuskripte: Person, die verantwortlich ist für die Ergänzung [`"[pointer]"`] | [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `figure` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-figure.html), [DTABf](abbKennzeichnung.html) | Abbildung | `@facs` | Link zu einer Darstellung der Original-Abbildung [`"[pointer]"`] | [floats](legende.html#legende__fk05) | [1 (notwendig)](legende.html#legende__l01) |
| `@type` | Art der Abbildung [`"notatedMusic"`] |
| `floatingText` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-floatingText.html), [DTABf](brEinschub.html) | unterbrechender Textabschnit |  | | [floats](legende.html#legende__fk05) | [2 (empfohlen)](legende.html#legende__l02) |
| `foreign` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-foreign.html), [DTABf](fremdsprachlMaterial.html) | fremdsprachliches Material | `@xml:lang` | Sprachcode (ISO 639-3) | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `formula` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-formula.html), [DTABf](formelnAllg.html) | Formel | `@facs` | verweist auf eine graphische Darstellung der Formeltranskription | [floats](legende.html#legende__fk05), [phraseStructure](legende.html#legende__fk07) | [1 (notwendig)](legende.html#legende__l01) |
| `@notation` | Art der Notierung [`"MathML"`, `"TeX"`] |
| `front` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-front.html), [DTABf](TEIStruktur.html), [DTABf2](frontAllg.html), | Titelei (Werk) |  | | [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `fw` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-fw.html), [DTABf](ohAllg.html) | Elemente der Druckplatte | `@place` | Position [`"bottom"`, `"top"`] | [floats](legende.html#legende__fk05) | [2 (empfohlen)](legende.html#legende__l02) |
| `@type` | Art des Elements [`"catch"`, `"header"`, `"pageNum"`, `"sig"`] |
| `g` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-g.html) | Sonderzeichen (außerhalb von Unicode) | *stattdessen U+FFFC benutzen* | | [phraseStructure](legende.html#legende__fk07) | [4 (unzulässig)](legende.html#legende__l04) |
| `gap` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-gap.html), [DTABf](gapSupplied.html) | fehlendes Textmaterial | `@quantity` | Umfang des Textverlusts | [editorial](legende.html#legende__fk04) | [1 (notwendig)](legende.html#legende__l01) |
| `@reason` | Grund des Textverlusts [`"fm"`, `"illegible"`, `"insignificant"`, `"lost"`] |
| `@unit` | Einheit, in welcher der Umfang des Textverlusts angegeben wird [`"chars"`, `"lines"`, `"pages"`, `"words"`] |
| `head` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-head.html), [DTABf](div.html), [DTABf2](tabAllg.html), [DTABf3](liAllg.html), [DTABf4](abbKennzeichnung.html), [DTABf5](geProsa.html), | Überschrift |  | | [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `hi` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-hi.html), [DTABf](typogrAllg.html) | Hervorhebung | `@rendition` | das Mittel der Hervorhebung | [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `imprimatur` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-imprimatur.html), [DTABf](tbAllg.html) | Druckgenehmigung |  | | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `item` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-item.html), [DTABf](liAllg.html) | Listenelement |  | | [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `l` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-l.html), [DTABf](geProsa.html), [DTABf2](geLyrikband.html) | Zeile bzw. Vers | `@n` | Versnummer (aus der Vorlage) | [textStructure](legende.html#legende__fk09), [verse](legende.html#legende__fk11) | [1 (notwendig)](legende.html#legende__l01) |
| `label` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-label.html) | Einleitung eines Postscriptums | *sollte mit im  [`postscript`](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-postscript.html) stehen* | | [letter](legende.html#legende__fk06), [phraseStructure](legende.html#legende__fk07) | [4 (unzulässig)](legende.html#legende__l04) |
| `lb` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-lb.html), [DTABf](lbAllg.html) | Zeilenumbruch | `@n` | gedruckte Zeilennummer | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `lg` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-lg.html), [DTABf](geProsa.html) | Gruppe von Versen | `@n` | (bei Strophen:) Strophennummer | [verse](legende.html#legende__fk11), [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `@type` | Art der Versgruppe [`"poem"`] |
| `list` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-list.html), [DTABf](liAllg.html) | Liste |  | | [floats](legende.html#legende__fk05), [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `listBibl` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-listBibl.html), [DTABf](bibliographie.html) | Liste bibliographischer Angaben |  | | [textStructure](legende.html#legende__fk09) | [3 (fakultativ)](legende.html#legende__l03) |
| `metamark` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-metamark.html), [DTABf](msEinweisung.html) | Einweisung durch den Autor | nur in Manuskripten zu verwenden | | [manuscripts](legende.html#legende__fk12), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `milestone` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-milestone.html), [DTABf](horizontaleLinie.html) | Text-/Abschnittsseparator | `@rendition` | Gestalt der Textunterbrechung [`"#hr"`, `"#hrBlue"`, `"#hrRed"`, `"#vr"`] | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `@unit` | Textunterbrechung (horizontale Linie) [`"section"`] |
| `name` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-name.html), [DTABf](eigenname.html) | Eigenname (alles außer Personen, Orte und Organisationen) | `@full` | Vollständigkeit des Namens [`"abb"`] | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `@ref` | Referenz auf eine Ressource, die den jeweiligen Eigennamen näher spezifiziert [`"[URI]"`] |
| `@type` | Art des Eigennamens [`"artificialWork"`] |
| `note` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-note.html), [DTABf](marginalie.html), [DTABf2](fussnote.html), [DTABf3](endnote.html), [DTABf4](sachkommentar.html) | Anmerkung (Fußnote, Endnote, Marginalie) | `@n` | Fuß-/Endnotenzeichen/-nummer | [floats](legende.html#legende__fk05) | [1 (notwendig)](legende.html#legende__l01) |
| `@place` | Position [`"end"`, `"foot"`, `"left"`, `"right"`] |
| `@type` | Art der Anmerkung [`"editorial"`] |
| `opener` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-opener.html), [DTABf](brAllg.html) | Briefbeginn/-kopf |  | | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `orgName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-orgName.html), [DTABf](eigenname.html) | Eigenname (Organisation) | `@full` | Vollständigkeit des Namens [`"abb"`] | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `@ref` | Referenz auf eine Ressource, die den jeweiligen Eigennamen näher spezifiziert [`"[URI]"`] |
| `orig` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-orig.html), [DTABf](normalisierung.html) | (bei Normalisierungen:) der Vorlage entsprechende Schreibung |  | | [phraseStructure](legende.html#legende__fk07), [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `p` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-p.html), [DTABf](absatz.html) | Absatz |  | | [textStructure](legende.html#legende__fk09) | [1 (notwendig)](legende.html#legende__l01) |
| `pb` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-pb.html), [DTABf](seitenFacsNr.html) | Seitenumbruch | `@facs` | Verweis auf Faksimile | [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `@n` | Seitennummer |
| `persName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-persName.html), [DTABf](eigenname.html) | Eigenname (Person) | `@full` | Vollständigkeit des Namens [`"abb"`] | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `@ref` | Referenz auf eine Ressource, die den jeweiligen Eigennamen näher spezifiziert [`"[URI]"`] |
| `placeName` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-placeName.html), [DTABf](eigenname.html) | Eigenname (Ort) | `@full` | Vollständigkeit des Namens [`"abb"`] | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `@ref` | Referenz auf eine Ressource, die den jeweiligen Eigennamen näher spezifiziert [`"[URI]"`] |
| `postscript` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-postscript.html), [DTABf](brPostscriptum.html) | Postskriptum (Brief) | `@n` | (bei mehreren Postscripta:) Nummer | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `publisher` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-publisher.html), [DTABf](tbAllg.html) | Herausgeber/Drucker |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `pubPlace` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-pubPlace.html), [DTABf](tbAllg.html) | Veröffentlichungsort |  | | [titlepage](legende.html#legende__fk10) | [2 (empfohlen)](legende.html#legende__l02) |
| `q` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-q.html) | wörtliche Rede |  | | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `quote` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-quote.html), [DTABf](zitateEpigraphe.html) | (im Zitat:) Zitattext | `@type` | Art des Zitattexts [`"translation"`] | [citations](legende.html#legende__fk01), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `ref` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-ref.html), [DTABf](inhaltsverzeichnis.html), [DTABf2](anhRegEinfach.html), [DTABf3](sachkommentar.html) | Verweis | `@target` | Referenz auf eine Ressource [`"[URI]"`] | [phraseStructure](legende.html#legende__fk07) | [3 (fakultativ)](legende.html#legende__l03) |
| `@type` | Textpassage, auf die sich ein editorischer Kommentar bezieht [`"editorialNote"`] |
| `reg` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-reg.html), [DTABf](normalisierung.html) | (bei Normalisierungen:) regularisierte Form |  | | [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `role` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-role.html), [DTABf](drFiguren.html) | Rollenname | `@xml:id` | ID für eine Rolle (Drama) | [drama](legende.html#legende__fk03), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `roleDesc` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-roleDesc.html), [DTABf](drFiguren.html) | Beschreibung einer Rolle (Drama) |  | | [drama](legende.html#legende__fk03), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `row` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-row.html), [DTABf](tabAllg.html) | Tabellenzeile |  | | [tables](legende.html#legende__fk08) | [1 (notwendig)](legende.html#legende__l01) |
| `s` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-s.html) | ein Satz | *wird im DTA-Korpus standoff annotiert* | | [phraseStructure](legende.html#legende__fk07) | [4 (unzulässig)](legende.html#legende__l04) |
| `salute` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-salute.html), [DTABf](brAllg.html) | Grußformel (Brief) |  | | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `seg` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-seg.html) | Textsegment | *stattdessen @corresp, @prev und @next benutzen* | | [textStructure](legende.html#legende__fk09), [documentStructure](legende.html#legende__fk02) | [4 (unzulässig)](legende.html#legende__l04) |
| `sic` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-sic.html), [DTABf](eeDruckfehler.html) | (bei Korrekturen:) inkorrekte Schreibweise in der Vorlage |  | | [phraseStructure](legende.html#legende__fk07), [editorial](legende.html#legende__fk04) | [3 (fakultativ)](legende.html#legende__l03) |
| `signed` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-signed.html), [DTABf](brAllg.html) | Unterschrift, Signatur (Brief) |  | | [letter](legende.html#legende__fk06), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `sp` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-sp.html), [DTABf](drSprechaktRede.html) | Sprechakt | `@who` | Sprecher-ID (wie der Rolle zugewiesen) | [drama](legende.html#legende__fk03), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `space` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-space.html), [DTABf](msPlatzhalter.html) | signifikanter Leerraum | `@dim` | Ausdehnung [`"horizontal"`, `"vertical"`] | [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `@quantity` | Umfang des Leerraums |
| `@unit` | Einheit, in welcher der Umfang des Leerraums angegeben wird [`"chars"`, `"lines"`, `"words"`] |
| `speaker` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-speaker.html), [DTABf](drSprechaktRede.html) | Sprecher eines Sprechaktes (Drama) |  | | [drama](legende.html#legende__fk03) | [2 (empfohlen)](legende.html#legende__l02) |
| `spGrp` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-spGrp.html), [DTABf](drSprechaktGruppe.html) | Gruppe von Sprechakten |  | | [drama](legende.html#legende__fk03), [textStructure](legende.html#legende__fk09) | [2 (empfohlen)](legende.html#legende__l02) |
| `stage` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-stage.html), [DTABf](drBuehnenanweisung.html) | Bühnenanweisung |  | | [drama](legende.html#legende__fk03) | [2 (empfohlen)](legende.html#legende__l02) |
| `subst` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-subst.html), [DTABf](msSubst.html) | Ersetzung durch den Autor | nur in Manuskripten zu verwenden | | [manuscripts](legende.html#legende__fk12), [phraseStructure](legende.html#legende__fk07) | [2 (empfohlen)](legende.html#legende__l02) |
| `supplied` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-supplied.html), [DTABf](gapSupplied.html) | bei Transkription ergänzter Text | `@resp` | Person, die verantwortlich ist für eine Ergänzung [`"[pointer]"`] | [editorial](legende.html#legende__fk04) | [1 (notwendig)](legende.html#legende__l01) |
| `@cert` | [`"high"`, `"low"`] |
| `table` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-table.html), [DTABf](tabAllg.html) | Tabelle |  | | [floats](legende.html#legende__fk05) | [1 (notwendig)](legende.html#legende__l01) |
| `titlePage` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-titlePage.html), [DTABf](tbAllg.html) | Titelseite innerhalb der Titelei | `@type` | Art der Titelseite [`"halftitle"`, `"heading"`, `"main"`, `"series"`] | [documentStructure](legende.html#legende__fk02) | [1 (notwendig)](legende.html#legende__l01) |
| `titlePart` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-titlePart.html), [DTABf](tbAllg.html) | Teil eines Titels | `@type` | Art des Titelteils [`"copyright"`, `"dedication"`, `"desc"`, `"main"`, `"price"`, `"series"`, `"sub"`, `"volume"`] | [titlepage](legende.html#legende__fk10) | [1 (notwendig)](legende.html#legende__l01) |
| `trailer` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-trailer.html), [DTABf](nachsatz.html) | beschließender Text am Ende einer Texteinheit |  | | [textStructure](legende.html#legende__fk09) | [3 (fakultativ)](legende.html#legende__l03) |
| `w` Doku: [TEI](http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-w.html) | ein Wort | *wird im DTA-Korpus standoff annotiert* | | [phraseStructure](legende.html#legende__fk07) | [4 (unzulässig)](legende.html#legende__l04) |


---

## Das DTABf im Überblick

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/uebersichten.html](https://www.deutschestextarchiv.de/doku/basisformat/uebersichten.html)

# Das DTABf im Überblick

Das Tagset im Überblick

Die folgenden Tabellen bieten einen Überblick über alle Elemente, die das DTA-Basisformat für den [<teiHeader>](uebersichtHeader.html)- bzw. den [<text>](uebersichtText.html)-Bereich vorsieht.

## Themen

* [Elemente im Header-Bereich](uebersichtHeader.html)
* [Elemente im Text-Bereich](uebersichtText.html)
* [Legende](legende.html)


---

## Wechsel zur Antiquaschrift

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/wechselAntiqua.html](https://www.deutschestextarchiv.de/doku/basisformat/wechselAntiqua.html)

# Wechsel zur Antiquaschrift

## Kodierung des Wechsels zur Antiquaschrift

![](img/WZxEDkBMlE.png)

```
die <hi rendition="#aq">differentia specifica</hi> der Religion.
```

*Quelle: [Feuerbach, Ludwig: Das Wesen des Christentums. Leipzig,
1841. [Faksimile 36]](http://www.deutschestextarchiv.de/feuerbach_christentum_1841/36)*

Antiquapassagen werden nur dann gesondert ausgezeichnet, wenn sie innerhalb von
Frakturtexten auftreten. Auch innerhalb eines Wortes kann es zum Wechsel zwischen Antiqua und
Fraktur kommen.


---

## Widmungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/widmung.html](https://www.deutschestextarchiv.de/doku/basisformat/widmung.html)

# Widmungen

Widmungen stehen in der Regel am Beginn eines Buches und somit innerhalb des `<front>`-
Elements.

```
<div type="dedication">
  <p>[Widmungstext]</p>
</div>
```


---

## Zitate

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeAllg.html](https://www.deutschestextarchiv.de/doku/basisformat/zeAllg.html)

# Zitate

Zitate werden systematisch immer dann
ausgezeichnet, wenn sie deutlich vom Fließtext abgesetzt erscheinen.

HINWEIS:

***Abweichende Regelung Phase 1:**Zitate werden systematisch immer dann
ausgezeichnet, wenn sowohl das Zitat als auch die Angabe des
Erfassers deutlich vom Fließtext abgesetzt erscheinen.*

Inline-Zitate werden zunächst nicht ausgezeichnet. In einem zweiten
Bearbeitungsschritt kann die Angabe, dass es sich um ein Zitat
handelt, jeweils nachgepflegt werden. Eine systematische
Auszeichnung von Inline-Zitaten im DTA-Korpus erfolgt jedoch nicht.


---

## Auszeichnung von Zitaten mit Nennung des Urhebers

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeMitAutor.html](https://www.deutschestextarchiv.de/doku/basisformat/zeMitAutor.html)

# Auszeichnung von Zitaten mit Nennung des Urhebers

Zitate mit Nennung des Urhebers werden mittels
`<cit>` ausgezeichnet. Der eigentliche
Zitattext steht innerhalb eines
`<quote>`-Elements. Der Urheber des Zitats wird
in `<bibl>` angegeben. Die Reihenfolge, in
welcher die Elemente `<quote>` und
`<bibl>` stehen, folgt den Gegebenheiten der
Vorlage.

*Zitat mit Nennung des Urhebers (beispielhaft):*

```
<cit>
  <quote>[Zitattext]</quote>
  <bibl>[Urheber des Zitats]</bibl>
</cit>
```

## Zitat mit Autor (1)

![](img/GsTu4qwSiQ.png)

```
<cit rendition="#et">
    <quote>
      <hi rendition="#i">
        <hi rendition="#aq">As if increaſe of appetite had grown<lb/>By what it fed on —</hi>
      </hi>
    </quote><lb/>
    <bibl>
      <hi rendition="#aq #k">Shakespear.</hi>
    </bibl>
</cit><lb/>
```

*Quelle: [Forster, Georg: Johann Reinhold
Forster's [...] Reise um die Welt. Bd. 1. Berlin, 1778.
[Faksimile 160]](http://www.deutschestextarchiv.de/forster_reise01_1778/160)*

## Zitat mit Autor (2)

![](img/hsObmpOqPB.png)

```
<cit rendition="#et #aq">
      <quote>Friend to mankind, she glitters from afar,<lb/>Now the bright ev’ ning, now the morning star.</quote><lb/>
      <bibl>Baker.</bibl>
</cit><lb/>
```

*Quelle: [Littrow, Joseph Johann von: Die
Wunder des Himmels, oder gemeinfaßliche Darstellung des
Weltsystems. Bd. 2. Stuttgart, 1835. [Faksimile
74]](http://www.deutschestextarchiv.de/littrow_weltsystem02_1835/74)*


---

## Auszeichnung von Zitaten ohne Nennung des Urhebers

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeOhneAutor.html](https://www.deutschestextarchiv.de/doku/basisformat/zeOhneAutor.html)

# Auszeichnung von Zitaten ohne Nennung des Urhebers

Zitate ohne Nennung des Urhebers werden mit dem
`<quote>`-Element umschlossen.

```
<quote>[Zitattext]</quote>
```

## Zitate ohne Autornennung

![](img/b211EJRiDk.png)

```
<p>[...] Wer die Sonne lange anſieht, wird blind; wer<lb/>
  Meduſa betrachtete, wurde Stein; wer aber Lucrezien’s Angeſicht<lb/>
  ſchaut:<lb/>
    <quote>
      <hi rendition="#c #aq">Fit primo intuitu cæcus et inde lapis.</hi>
    </quote><lb/>
  Ja der marmorne ſchlafende Cupido in ihren Sälen ſoll von ihrem<lb/>
  Blick verſteinert ſein:<lb/>
    <quote>
      <hi rendition="#c #aq">Lumine Borgiados saxificatus Amor.</hi>
    </quote>
</p><lb/>
```

*Quelle: [Burckhardt, Jacob: Die Cultur der
Renaissance in Italien. Ein Versuch. Basel, 1860. [Faksimile
354]](http://www.deutschestextarchiv.de/burckhardt_renaissance_1860/354)*


---

## Übersetzungen von Zitaten

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeUebersetzung.html](https://www.deutschestextarchiv.de/doku/basisformat/zeUebersetzung.html)

# Übersetzungen von Zitaten

Ist einem Zitat in Originalsprache eine Übersetzung beigegeben, so
wird diese Übersetzung ebenfalls mit dem Element
`<quote>` umschlossen. Ein möglicherweise der
Übersetzung beigegebener Autor wird in einem
`<bibl>`-Element angegeben. Beide Teile
(`<quote>` und `<bibl>`)
werden mit einem `<cit>`-Element umschlossen.
(Vgl. die [Hinweise zur Auszeichnung von Zitaten mit Nennung des Autors](zeMitAutor.html)
bzw. [ohne Nennung des
Autors](zeOhneAutor.html).)

Das Element `<quote>` der Übersetzung erhält ein
Attribut-Wert-Paar `@type="translation"`. Das Element
`<quote>` des Originalzitats erhält ein
Attribut-Wert-Paar `@xml:lang="[ISO 639-3 Code]"`, in
welchem die Sprache spezifiziert ist. (Zur Auszeichnung
fremdsprachlichen Materials s. unten Kap. [Fremdsprachliches Material](inlineAnnotation.html).)

Beide `<quote>`-Elemente (Originalzitat und
dessen Übersetzung) werden mittels `@xml:id` und
`@corresp` miteinander verknüpft.

```
<cit>
  <quote xml:lang="[ISO 639-3 Code]" xml:id="[ID-Originalzitat]" corresp="[ID-Übersetzung]">[Zitat in Originalsprache]</quote>
  <bibl>[Urheber des Zitats]</bibl>
</cit>
<cit><!-- gegebenenfalls -->
  <quote type="translation" xml:id="[ID-Übersetzung]" corresp="[ID-Originalzitat]">[Zitat in Übersetzung]</quote>
  <bibl>[Urheber des Zitats/der Übersetzung]</bibl><!-- gegebenenfalls -->
</cit>

```

## Kodierung von übersetzten Zitaten

![](img/NVwr1q5NEH.png)![](img/ZM1qb4lx9Z.png)

```
<quote corresp="qte2b" xml:id="qte2a" xml:lang="lat">
  <hi rendition="#aq">Laudatas oſtentat auis Iunonia pennas.<lb/>
  Si tacite ſpectes, illa recondit opes.</hi>
</quote><lb/>
<p>
  <hi rendition="#c">Das iſt/</hi>
</p><lb/>
<pb n="266" facs="#f0276"><lb/>
<quote type="translation" corresp="#qte2a" xml:id="qte2b">
  <lg type="poem">
    <l>Wenn du den Pfawen wirſt hoch ru&#x0364;hmen/</l><lb/>
    <l>So zeigt er dir ſeins Schwantzes Blumen.</l><lb/>
    <l>Bleibſtu aber ſtillſchweigend beſtehen/</l><lb/>
    <l>So leſt er ſeinen Schatz nicht ſehen.</l>
  </lg>
</quote><lb/>
            
```

*Quelle a: [Rollenhagen, Gabriel: Vier Bücher
Wunderbarlicher biß daher vnerhörter/ vnd vngleublicher
Jndianischer reysen. Magdeburg, 1603. [Faksimile 275]](http://www.deutschestextarchiv.de/rollenhagen_reysen_1603/275)*

*Quelle b: [Ebd. [Faksimile 276]](http://www.deutschestextarchiv.de/rollenhagen_reysen_1603/276)*


---

## Zitate/Epigraphe als Versgruppen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeVers.html](https://www.deutschestextarchiv.de/doku/basisformat/zeVers.html)

# Zitate/Epigraphe als Versgruppen

Ist das Zitat/Epigraph in Versen geschrieben, so wird es außerdem als
`<lg>` gekennzeichnet:

```
<epigraph> <!-- sofern vorhanden -->
  <cit>
    <quote>
      <lg>
        <head>[Titel]</head> <!-- sofern vorhanden -->
        <l>[Vers]</l>
        <l>[Vers]</l>
      </lg>
    </quote>
    <bibl>[Urheber des Gedichts]</bibl> <!-- sofern vorhanden -->
  </cit>
</epigraph>
```

## Kodierung von Zitaten in Versform

![](img/Od5z6vJ6Ec.png)

```
<epigraph>
  <cit rendition="#et">
    <quote>
      <lg>
        <l>Hier quillt die träumeriſche,</l><lb/>
        <l>Urjugendliche Friſche;</l><lb/>
        <l>In ahnungsvoller Hülle</l><lb/>
        <l>Die ganze Lebensfülle.</l>
      </lg>
    </quote>
    <bibl><hi rendition="#g">Lenau</hi></bibl>.
  </cit>
</epigraph><lb/>
```

*Quelle: [Roßmäßler, Emil Adolf: Der Wald. Leipzig u. a., 1863. [Faksimile 33]](http://www.deutschestextarchiv.de/rossmaessler_wald_1863/33)*


---

## Zeilen- und Versnummerierungen

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeilenVersNr.html](https://www.deutschestextarchiv.de/doku/basisformat/zeilenVersNr.html)

# Zeilen- und Versnummerierungen

Zeilennummerierungen in Prosatexten werden mittels des Attributs `@n`
innerhalb des Elements `<lb>` wiedergegeben. Da das `<lb>`-Element den Schluss einer
Zeile markiert, bezieht sich der Wert von `@n` auf die zugehörige vorangehende
Zeile.

```
[Text Zeile 10]<lb n="10"/>
```

## Kodierung von Zeilennummerierungen

![](img/dplhbutpxN.png)

```
Blickend, kühlt’ ihr die Rechte mit grü-<lb/>nem Fächer das Antliz;<lb n="105"/>
```

*Quelle:
[Voß, Johann Heinrich: Luise. Ein ländliches Gedicht in 3 Idyllen. Königsberg, 1795. [Faksimile 29]](http://www.deutschestextarchiv.de/voss_luise_1795/29)*

Versnummerierungen in Gedichten werden
mittels des Attributs `@n` innerhalb des Elements `<l>`
wiedergegeben. Sie stehen somit am Beginn der Zeile, auf welche sie sich beziehen.

## Kodierung von Versnummerierungen

![](img/hhPK3kXLXo.png)

```
<lg type="poem">
  <l>Vier Jahrhunderte ſind geſchwunden,</l><lb/>
  <l>Seit du die ſchwarze Kunſt erfunden;</l><lb/>
  <l>Was hat ſie der Welt für Gewinn gebracht?</l><lb/>
  <l n="4">Den Bücherhaufen größer gemacht.</l>
</lg><lb/>
```

*Quelle:
[Sanders, Daniel: Aus der Werkstatt eines Wörterbuchschreibers. Plaudereien. Berlin, 1889. [Faksimile 64]](http://www.deutschestextarchiv.de/sanders_woerterbuchschreiber_1889/64)*

Tipp:

Zur Strukturierung von Gedichten s. auch Kap. [Gedichte](gedichte.html).

Die Position der Zeilen- bzw. Versnummerierung rechts oder links der Zeile/des Verses
wird nicht angegeben.

Zeilen- und Vernummerierungen werden in der Regel aus der Vorlage
übernommen. Ergänzende Nummerierungen des Bearbeiters stehen in eckigen Klammern.

## Kodierung ergänzender Versnummerierungen

![](img/z5mRG7prAC.png)

```
<l n="[1]">Vier Jahrhunderte ſind geſchwunden,</l><lb/>
<l n="[2]">Seit du die ſchwarze Kunſt erfunden;</l><lb/>
<l n="[3]">Was hat ſie der Welt für Gewinn gebracht?</l><lb/>
<l n="4">Den Bücherhaufen größer gemacht.</l><lb/>
```

*Quelle:
[Sanders, Daniel: Aus der Werkstatt eines Wörterbuchschreibers. Plaudereien. Berlin, 1889. [Faksimile 64]](http://www.deutschestextarchiv.de/sanders_woerterbuchschreiber_1889/64)*


---

## Zeilenumbrüche

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeilenumbruch.html](https://www.deutschestextarchiv.de/doku/basisformat/zeilenumbruch.html)

# Zeilenumbrüche

## Themen

* [Zeilenumbrüche Grundstruktur](lbAllg.html)
* [Silbentrennung](silbentrennung.html)
* [Zeilen- und Versnummerierungen](zeilenVersNr.html)


---

## Auszeichnung von Zeitungen und Periodika

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zeitung.html](https://www.deutschestextarchiv.de/doku/basisformat/zeitung.html)

# Auszeichnung von Zeitungen und Periodika

## Themen

* [Zeitungen Grundregeln](jAllg.html)
* [Einleitende Textstücke](jFront.html)
* [Textkörper](jBody.html)
* [Abschließende Textstücke](jBack.html)
* [Beilagen](jBeilagen.html)


---

## Ziel und Fokus des DTA-Basisformats

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/ziel.html](https://www.deutschestextarchiv.de/doku/basisformat/ziel.html)

# Ziel und Fokus des DTA-Basisformats

Die folgende Darstellung dokumentiert das XML-Basisformat des DTA, welches
die Grundlage für die Annotation der DTA-Volltexte bildet. Das DTA-Basisformat
folgt den P5-Richtlinien der [Text Encoding
Initiative](http://www.tei-c.org/) (TEI). Da diese Richtlinien jedoch Lösungen für
sämtliche Bedürfnisse bei der Textaufbereitung anbieten sollen und daher
entsprechend vielfältig und umfangreich sind, bedürfen sie im konkreten
Einzelfall einer näheren Spezifikation. Daher wurde aus den P5-Richtlinien
für die Textstrukturierung im DTA-Korpus eine Tag-Auswahl getroffen (Tagset),
die das DTA-Basisformat bildet. Dieses Tagset ist mit den P5-Richtlinien der
TEI vollständig konform; auf Erweiterungen (tei.extensions) durch davon
abweichende Elemente wurde verzichtet.

Das DTA-Basisformat soll im Rahmen der DTA-Richtlinien, die daneben auch die allgemeinen [Leitlinien des
DTA](http://www.deutschestextarchiv.de/doku/leitlinien) sowie die [Transkriptionsrichtlinien](http://www.deutschestextarchiv.de/doku/richtlinien) umfassen, eine umfassende Textaufbereitung ermöglichen
und dabei gleichzeitig Variationsspielräume bei der Annotation so einschränken, dass die Kohärenz der
DTA-Texte untereinander gewährleistet wird. Für dieses Ziel stellt die weite zeitliche Erstreckung des
DTA-Korpus einerseits und seine Textsortenvielfalt andererseits eine große Herausforderung dar, resultiert
sie doch u. a. in einer strukturellen Variabilität der Vorlagen, der mit dem zur Verfügung stehenden Tagset
Genüge getan werden muss.

Mit der Ausarbeitung des DTA-Basisformats wollen wir einen Vorschlag
für einen Standard zur Volltext-Aufbereitung historischer Texte
unterbreiten. Damit soll die Analyse unterschiedlicher TEI-Texte mit
einheitlichen Methoden und im Vergleich miteinander ermöglicht werden. Die
DTABf-Annotationsrichtlinien sind ausführlich dokumentiert, um so
Ambiguitäten und folglich Fehlinterpretationen der
Auszeichnungsmöglichkeiten weiter zu minimieren. Somit sollen zum einen
Texte, die mit dem Basisformat kompatibel sind, in das DTA einfließen
können, zum anderen aber die Verwendung von DTA-Texten in anderen
Volltextarchiven erleichtert werden.

Das DTA-Basisformat wurde von der DFG und CLARIN-D zur Nachnutzung empfohlen, namentlich in den folgenden Dokumenten:

* [Handreichung: Empfehlungen zu datentechnischen Standards und Tools
  bei der Erhebung von Sprachkorpora](https://www.dfg.de/resource/blob/171632/383249f00d425a643bd8c120404bbff6/standards-sprachkorpora-data.pdf). Hrsg. vom Fachkollegium Sprachwissenschaften der
  Deutschen Forschungsgemeinschaft (DFG). Bonn 2019.
* [Förderkriterien für wissenschaftliche Editionen in der
  Literaturwissenschaft.](https://www.dfg.de/resource/blob/172106/3098d74057d3e0c82fdc1dd7e1b10480/foerderkriterien-editionen-literaturwissenschaft-data.pdf) Hrsg. vom Fachkollegium Literaturwissenschaft der Deutschen
  Forschungsgemeinschaft (DFG). Bonn 2015.
* [CLARIN-D User
  Guide.](https://doi.org/10.5281/zenodo.15024961) Part II (Linguistic resources and tools), ch. 6 (Types of resources), section
  "Text Corpora". Hrsg. von CLARIN-D AP 5. Berlin 2012.


---

## Zitate und Epigraphe

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zitateEpigraphe.html](https://www.deutschestextarchiv.de/doku/basisformat/zitateEpigraphe.html)

# Zitate und Epigraphe

## Themen

* [Zitate](zeAllg.html)
* [Zitate ohne Nennung des Urhebers](zeOhneAutor.html)
* [Zitate mit Nennung des Urhebers](zeMitAutor.html)
* [Epigraphe](epigraphe.html)
* [Zitate/Epigraphe als Versgruppen](zeVers.html)
* [Übersetzungen von Zitaten](zeUebersetzung.html)


---

## Nutzung der DTABf-Dokumentation

Quelle: [https://www.deutschestextarchiv.de/doku/basisformat/zurDokumentation.html](https://www.deutschestextarchiv.de/doku/basisformat/zurDokumentation.html)

# Nutzung der DTABf-Dokumentation

## Konventionen der Dokumentation

XML-Elemente werden mittels spitzer Klammern als solche gekennzeichnet:
`<[Elementname]>`. Sie sind darüber hinaus durch
`Nichtproportionalschrift` vom restlichen Text abgesetzt.

Ebenso sind sämtliche Beispiele durch `Nichtproportionalschrift`
gekennzeichnet. Sie sind zudem jeweils gelb unterlegt.

Umschreibungen für potentielle Inhalte von Elementen oder Werte von Attributen werden
durch eckige Klammern dargestellt.

Attribute im Fließtext werden durch ein vorangestelltes `@`
gekennzeichnet.

Einrückungen in Beispielen dienen lediglich der besseren Anschaulichkeit in der
vorliegenden Dokumentation. Sie sind nicht Bestandteil der XML-Dokumente des
DTA.

## Hinweise zur Dokumentation

Die DTABf-Dokumentation ist in mehrere Dokumente untergliedert:

1. Die zentrale Dokumentation der Richtlinien zur Textauszeichnung bilden die Teile
   [Formale Erschließung des Volltextes](texterschliessung_formal.html "Auszeichnung von formalen Strukturen in Volltexten (Besonderheiten in Typographie und Layout)") und
   [Inhaltliche Erschließung des Volltextes](texterschliessung_inhaltlich.html "Auszeichnung von inhaltsbezogenen (logischen, konzeptuellen) Strukturen in Volltexten").
   Eine eigene ergänzende Dokumentation ist der [Auszeichnung von Zeitungen](zeitung.html)
   gewidmet.
2. Neben den Richtlinien zur Textauszeichnung umfasst das DTABf Richtlinien zur
   [Strukturierung der Metadaten](metadaten.html "Erfassung (Transkription) und Auszeichnung von Metadaten"), welche ebenfalls
   in einem eigenen Dokument beschrieben sind.
3. Tabellarische Übersichten geben einen schnellen Einblick in das Tagset des DTABf
   für die [Textauszeichnung](uebersichtText.html) sowie für die
   [Metadaten-Strukturierung](uebersichtHeader.html).
4. Ergänzt wird die DTABf-Dokumentation durch die
   [DTA-Richtlinien zur Texterfassung](transkription.html "Richtlinien zur Erfassung der Volltexte").
5. Eine [Vorlagedatei zum DTA-Basisformat](http://www.deutschestextarchiv.de/files/vorlage_basisformat.xml), welche die
   DTABf-Schemas sowie die wichtigsten Elemente enthält, erleichtert den Einstieg in die DTABf-konforme
   Texterstellung.

Die DTABf-Dokumentation enthält zwei Formen von Beispielen. Zum einen werden die
vorgestellten Strukturierungen beispielhaft vorgestellt, wobei die vorgesehenen
Elementinhalte in eckigen Klammern umschrieben werden. Zum anderen sollen konkrete
Textbeispiele aus dem DTA-Korpus der Veranschaulichung dienen. Sie bestehen jeweils
aus einem Bildausschnitt und dem entsprechenden Ausschnitt des zugehörigen
strukturierten DTA-Volltexts.

Gegebenenfalls wurde innerhalb der Dokumentation oder in Bezug auf die Beispiele
zwischen der ersten DTA-Projektphase einerseits sowie der zweiten und dritten DTA-Projektphase
andererseits (Phase 1: 2007–2010; Phase 2: 2010–2014; Phase 3: seit Juni 2014)
unterschieden. Solche abweichenden Dokumentationen für die Phase 1 sind an den jeweiligen
Stellen entsprechend gekennzeichnet mittels des Ausdrucks:

HINWEIS:

***Abweichende Regelung Phase 1***

Dieses Nebeneinander verschiedener Lösungsansätze ist
Folge einer grundlegenden Überarbeitung des DTA-Basisformats nach den Erfahrungen der ersten
Projektphase. Die beschlossenen Anpassungen werden sukzessive in das bestehende DTA-Korpus
eingefügt. Bis zum Abschluss dieser Überarbeitungsphase wird die Dokumentation der ursprünglichen
Strukturierungsregeln mit bereitgestellt.
