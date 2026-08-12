# Viewer-UI, kritisch-konstruktive Analyse

Datum 2026-08-12. Gegenstand `docs/viewer.html` mit `docs/assets/css/{tokens,base,viewer}.css` und den
UI-Strings in `docs/assets/js/`. Vergleichsblick auf `docs/index.html`. Der Bericht ordnet Befunde nach
Nutzerwirkung und schlägt je Befund die kleinste tragfähige Änderung vor. Implementiert wurde nichts.

## Vorbemerkung zur Belastbarkeit der Zeilenangaben

Die Analyse liest Markup, CSS und den JS-erzeugten DOM. Ein laufender Server wurde nicht bedient, es gab
keinen Klick und keinen Screenshot. Wo ein Befund aus dem Code erschlossen ist und eine Sichtprüfung
braucht, steht das ausdrücklich dabei.

Während der Analyse haben parallele Instanzen `docs/assets/js/viewer.js`, `docs/assets/js/tei-render.js`
und `docs/assets/css/viewer.css` unversioniert verändert (HEAD 631fa7c4, dazu ein uncommitteter Stand mit
einer neuen `xmlScope`-Umschaltung page/full). Alle Zeilenangaben sind gegen den Plattenstand zum
Analysezeitpunkt geprüft. Für die drei genannten Dateien ist die Zeilennummer eine Momentaufnahme;
maßgeblich bleibt der zitierte Selektor beziehungsweise der zitierte String. `viewer.html`, `base.css`,
`tokens.css` und `layout-editor.js` waren unverändert, dort sind die Nummern stabil.

## 1. Das Kernmuster hinter den vier Beobachtungen

Die vier Beobachtungen des Betriebs sind Symptome einer einzigen fehlenden Regel. Das Designsystem legt
Farbwerte, Typografie und Abstände fest, es legt aber nicht fest, welche Verschachtelungsebene eine Linie
zeichnen darf. Jede Komponente definiert sich deshalb selbst als abgeschlossene Einheit mit eigenem Rahmen,
und weil Komponenten ineinander sitzen, addieren sich die Rahmen.

Das erklärt die Querstriche und die Kästen in Kästen (Beobachtung 1). Es erklärt auch die Dichte
(Beobachtung 2), denn ein eigener Rahmen wirkt wie eine Erlaubnis, den umrahmten Bereich zu füllen. Und es
erklärt die redundanten Labels (Beobachtung 3), denn ein Kasten, der sich vom Rest absetzt, verlangt nach
einer Überschrift, die sagt, was in ihm steht, auch wenn der Inhalt für sich spricht. Die gewünschte ruhige
Hierarchie (Beobachtung 4) entsteht dadurch, dass Zusammengehörigkeit über Abstand und Flächenton
ausgedrückt wird und die Linie für den einen Schnitt reserviert bleibt, der wirklich zwei Bereiche trennt.

Positiv vorweg, damit die Rangliste richtig gelesen wird. Die Token-Disziplin hält. In `viewer.css` und
`base.css` steht kein einziger Hex-Wert und keine rohe `rgba()`-Angabe, alle Farben kommen aus `--h-*`.
Reines Schwarz oder Weiß kommt nirgends vor. Die Befunde in Abschnitt 5 betreffen die Semantik der
Token-Wahl. Eine Umgehung des Katalogs kommt an keiner Stelle vor.

## 2. Inventar der sichtbaren Chrome

### 2.1 Die vertikale Kette im Lesemodus

Von oben nach unten zeichnet der Standardzustand ohne jede Nutzerinteraktion folgende waagerechte Linien.

| # | Linie | Fundstelle |
|---|---|---|
| 1 | `.site-header` border-bottom | `docs/assets/css/base.css:226` (Deklaration 228) |
| 2 | `.doc-subbar__inner--status` border-top | `docs/assets/css/viewer.css:75` (Deklaration 76) |
| 3 | `.doc-subbar` border-bottom | `docs/assets/css/viewer.css:33` (Deklaration 35) |
| 4 | `.panel` Rahmen oben, zweimal nebeneinander | `docs/assets/css/viewer.css:267` (Deklaration 272) |
| 5 | `.panel__header` border-bottom, zweimal | `docs/assets/css/viewer.css:280` (Deklaration 285) |
| 6 | `.panel` Rahmen unten, zweimal | `docs/assets/css/viewer.css:267` |
| 7 | `.tei-legend` border-bottom, sobald Markup- oder Entity-Modus an ist | `docs/assets/css/viewer.css:648` (Deklaration 654) |
| 8 | `.site-footer` border-top | `docs/assets/css/base.css:322` (Deklaration 323) |

Acht waagerechte Kanten auf der Vertikalen, bevor eine einzige Zeile Transkription gelesen ist. Die
Positionen 1 bis 3 stapeln drei Bänder innerhalb der oberen rund 140 Pixel. Zwischen Band 2 und Band 3
liegen nach `docs/assets/css/viewer.css:75` nur `padding-top: 6px` und `padding-bottom: 6px`, also eine
Linie, sechs Pixel Luft, Inhalt, sechs Pixel Luft, wieder eine Linie.

### 2.2 Verschachtelung innerhalb eines Panel-Headers

Der Header des Textpanels (`docs/viewer.html:132-149`) sitzt in einem gerahmten Panel und zieht selbst eine
Unterkante. In ihm stehen fünf weitere gerahmte Elemente.

- `.toolbar__mode` mit eigenem Rahmen und eigenem Flächenton, `docs/assets/css/viewer.css:204` (Deklaration 210)
- vier Schalter `.panel__edit-toggle` mit je eigenem Rahmen, `docs/assets/css/viewer.css:311` (Deklaration 313), im Markup unter `docs/viewer.html:140`, `142`, `144`, `146`

Damit zeichnen in einem einzigen waagerechten Streifen sieben Regeln eine Kante, den Panelrahmen und die
Header-Unterkante mitgezählt. Der Faksimile-Header (`docs/viewer.html:109-123`) verhält sich gleich mit vier
gerahmten Bedienelementen, zwei `.btn`, einem `.input` und einem `.panel__edit-toggle`.

### 2.3 Der Entity-Kasten als tiefste Verschachtelung

Im Entity-Modus entsteht die stärkste Staffelung des ganzen Werkzeugs. `.entity-worklist`
(`docs/assets/css/viewer.css:718`) trägt einen Vollrahmen und zusätzlich eine drei Pixel starke linke
Ockerkante. Darin bekommt jeder Eintrag `.entity-worklist__item` (`:738`, Deklaration 744) eine eigene
Oberkante, und in jedem Eintrag trägt `.entity-worklist__rule` (`:752`, Deklaration 755) nochmals einen
Rahmen. Das ergibt vier Rahmenebenen, gezählt ab dem Panel, für eine Liste, die schlicht mitteilt, welche
Kandidaten im Text nicht verortet werden konnten.

### 2.4 Flächentöne, die zusätzlich schachteln

Neben den Linien staffeln sich vier Hintergrundtöne ineinander. Der Seitengrund `--h-bg`, darin das Panel
mit `--h-bg-alt` links und `--h-surface` rechts (`docs/assets/css/viewer.css:277-278`), darin der Textkörper
mit `--h-paper` (`:344`). Panel-Rahmen, Eckenradius und `box-shadow` (`:272-274`) markieren dieselbe Grenze
ein viertes Mal. Für die Trennung zweier Panels genügt eine dieser vier Auszeichnungen.

Dazu kommen `.panels` mit `padding: var(--h-space-lg) var(--h-space-xl)` (`:255`, Deklaration 263), also
eine bereits vorhandene Rinne um die Panels, die die Trennung ohnehin leistet.

## 3. Die drei Aufgaben

### 3.1 Eine Seite gegen das Faksimile lesen

Das ist die häufigste Aufgabe und die am stärksten beeinträchtigte.

Was die Aufgabe nicht braucht und trotzdem dauerhaft sieht. Die gesamte Statuszeile mit dem Label
`"Workflow"` (`docs/viewer.html:65`) und den drei Pills ist Buchhaltung auf Dokumentebene und für das Lesen
einer Seite ohne Belang. Der Initialen-Chip, die deaktivierte Schaltfläche `"Save"` und das
Export-Dropdown gehören zur Bearbeitung. Die Kopfzeile trägt Untertitel und Badge. Der Footer wiederholt,
was schon auf der Korpusseite steht.

Der schwerwiegendste Punkt betrifft das Faksimile selbst. Im Lesemodus zeichnet
`docs/assets/js/viewer.js:1225` die Layoutregionen unbedingt als Overlays über das Bild, sobald ein Layout
vorliegt und die Seite nicht leer ist. Jede Region bekommt nach `docs/assets/css/viewer.css:431`
(Deklaration 433) einen 1,5 Pixel starken farbigen Rahmen in der Farbe ihres Typs. Einen Schalter, der diese
Overlays im Lesemodus ausblendet, gibt es nicht; die Suche über `viewer.js` fördert keine
Sichtbarkeitsumschaltung zutage. Wer eine Seite gegen das Faksimile liest, liest sie also durch ein
dauerhaft eingeblendetes Raster farbiger Kästen. Verschärft wird das durch
`docs/assets/js/viewer.js:1245`, wo jede Region ein `title`-Attribut mit ihrem OCR-Text erhält, sodass die
Maus beim Lesen native Tooltips auslöst, und durch `.region:hover` mit Flächeneinfärbung
(`docs/assets/css/viewer.css`, Regel direkt nach `:431`).

Was die Aufgabe braucht und schwer zu finden ist. Die Seitennavigation sitzt im Faksimile-Panel-Header
(`docs/viewer.html:113-119`) rechts, in Konkurrenz zu `"Edit layout"`. Das Sprungfeld trägt den Platzhalter
`"p."` (`docs/viewer.html:118`). Die Tastaturbedienung existiert und ist wirksam, Pfeiltasten sowie Home und
End sind in `docs/assets/js/viewer.js` im Keydown-Handler gebunden, dokumentiert ist sie ausschließlich in
den `title`-Attributen zweier kleiner Schaltflächen. Wer nie hovert, erfährt nie davon.

### 3.2 Entitätskandidaten prüfen und entscheiden

Hier trifft Beobachtung 2 am deutlichsten zu.

Was gleichzeitig erscheint. Die Legende setzt sich im Entity-Modus aus `ENTITY_LEGEND` mit vier Zeilen
(`docs/assets/js/viewer.js:1588-1592`) und `MARKUP_LEGEND` ohne die generische Entity-Zeile zusammen
(`:1595`, Verkettung bei `:1620`), also aus bis zu elf Chips über dem Text. Für die Prüfung von Kandidaten
sind vier davon einschlägig. Die übrigen sieben, darunter `"Foreign"`, `"Footnotes"`, `"Editorial"`,
`"Unclear"`, `"Figures"`, `"Links"` und `"Sections"`, gehören zu einer anderen Frage. Darunter kann der
Kasten `.entity-worklist` stehen (`docs/assets/js/viewer.js:514-519`), dazu kommen die Unterstreichungen im
Text und das Popover beim Klick. Der Entity-Modus erzwingt zusätzlich die Markup-Hervorhebung, weil
`docs/assets/js/viewer.js:376` und `:418` `state.teiMarkup` auf `true` setzen.

Was der Aufgabe fehlt. Der Entity-Layer ist bewusst und durchgängig lesend, das Popover zeigt Herkunft und
Regel, eine Annahme- oder Ablehnungsgeste gibt es nicht. Die Aufgabe heißt aber prüfen und entscheiden. Die
Entscheidung findet damit außerhalb des Werkzeugs statt, und die Oberfläche sagt an keiner Stelle, wo.
Das ist eine bewusste Architekturentscheidung, kein Defekt, und gehört deshalb in Abschnitt 6.2.

Ein echter Defekt in dieser Aufgabe ist die Sprachmischung. Im selben Popover erzeugt
`docs/assets/js/viewer.js:579` für einen unentschiedenen Kandidaten den deutschen Text
`"nicht in der kuratierten Liste"`, während `:619` für den entschiedenen Fall den englischen Text
`"not in the curated entity list"` erzeugt. Dieselbe Aussage, zwei Sprachen, ein Popover. Gleiches Muster
in der Legende, wo `"Zur Prüfung"` (`:1592`) zwischen `"Persons"`, `"Organisations"` und `"Works"` steht,
sowie im Worklist-Kasten mit `"Nicht im Text verortet"` (`:522`) unter der englischen Bezeichnung
`aria-label="Worklist entries without a position in the text"` (`:519`).

### 3.3 Einen Strom bearbeiten und speichern

Was stört. Die Layout-Werkzeugleiste wird nach `docs/assets/css/viewer.css` (Kommentar bei `:234-239`)
bewusst in die Statuszeile gelegt, um eine Trennlinie zu sparen. Der Gewinn ist real, der Preis ist eine
Zeile, in der Workflow-Pills, Regionsschalter, Typ-Auswahl, zwei `.toolbar__divider` und vier
Koordinatenfelder um denselben Platz konkurrieren (`docs/viewer.html:63-99`). Beide beteiligten Container
tragen `flex-wrap: wrap` (`.status-controls` bei `:102` nachfolgend, `.editor-toolbar` bei `:240`
nachfolgend), das heißt die Zeile bricht bei schmalem Fenster still um und verschiebt das darunterliegende
Layout. Das ist aus dem Code erschlossen und braucht eine Sichtprüfung bei rund 1100 Pixel Fensterbreite.

Was schwer zu finden ist. Die Statuspills verändern das Manifest, gespeichert wird es von der Schaltfläche
`"Save"`, und zwischen beiden verläuft die Bandkante aus `docs/assets/css/viewer.css:75`. Der Hinweis
`"Unsaved status · Save"` (`docs/assets/js/viewer.js:765`) muss diese selbst gezogene Grenze verbal
überbrücken. Eine Linie, die einen Zusammenhang zerschneidet und dann durch Text repariert wird, ist die
klarste Einzelbegründung für Beobachtung 1.

Ein sachlicher Fehler steckt im Export-Tooltip. `docs/viewer.html:52` verspricht
`title="Download individual files / connect repo folder"`. Das Menü darunter (`docs/viewer.html:53-59`)
enthält vier Download-Einträge und keinen Eintrag zum Verbinden des Repo-Ordners; das Verbinden läuft
ausschließlich über den Speicherpfad und den Modaldialog. Passend dazu ist `.export-menu__sep`
(`docs/assets/css/viewer.css:1054`) definiert, wird aber von keiner Stelle in HTML oder JS erzeugt, was auf
einen entfernten zweiten Menüabschnitt hindeutet.

## 4. Inventar der statischen Erklärtexte

`docs/viewer.html` trägt 19 `title`-Attribute und 17 `aria-label`. Dazu kommen zur Laufzeit gesetzte Titel
für Statuspills, Speichern, Entities und die beiden Editierschalter.

### 4.1 Tragend, sagt etwas nicht Erschließbares

| Text | Fundstelle | Begründung |
|---|---|---|
| `"Experimental"` samt Tooltip | `docs/viewer.html:26-27` | Haftungsrelevante Aussage über den Status der Inhalte |
| Tooltip des Initialen-Chips | `docs/viewer.html:45` | Erklärt lokale Speicherung und Eintrag in jeden Speichervorgang |
| Modaltext zum Repo-Ordner | `docs/viewer.html:163-171` | Nennt Zielordner und Schreibpfade vor dem Systemdialog |
| `"Blank page, no text"` | `docs/assets/js/viewer.js:1194`, `:1359` | Unterscheidet gewollte Leerseite von fehlenden Daten |
| `"No annotations on this page"` | `docs/assets/js/viewer.js:1633` | Unterscheidet leere Seite von defekter Anzeige |
| Statuspill-Zeile für `unverifiziert` | `docs/assets/js/viewer.js:751` | Löst den Übergabe-Default auf, den die Farbe allein nicht trägt |
| `"TEI · XML (full document)"` | `docs/assets/js/viewer.js:1338` | Der Bearbeitungsumfang ist speicherrelevant |
| `ENTITY_READONLY_HINT` | `docs/assets/js/viewer.js:89` | Erklärt eine gesperrte Schaltfläche |

### 4.2 Ersetzbar, kann Tooltip werden oder in den Rand rücken

| Text | Fundstelle | Vorschlag |
|---|---|---|
| `"Reading order (drag to reorder, click to select)"` | `docs/assets/js/layout-editor.js:465` | Auf `"Lesereihenfolge"` kürzen, Bedienhinweis in `title` der Liste |
| `"Workflow"` | `docs/viewer.html:65` | Entfällt, sobald die Pills ihren Strom selbst benennen, was sie über `.status-pill__stream` bereits tun |
| `"BBox"` samt X, Y, W, H | `docs/viewer.html:92-96` | Das vorhandene `aria-label` der Gruppe genügt, die vier Felder sind durch ihre Buchstaben eindeutig |
| `"Single export (download)"` | `docs/viewer.html:54` | Entfällt, siehe 4.3 |
| Statuslegende der Korpusseite | `docs/index.html:79-84` | Dupliziert die Pill-Tooltips des Viewers; eine Quelle genügt |

### 4.3 Entfernbar, erklärt das Offensichtliche

| Text | Fundstelle | Begründung |
|---|---|---|
| `"Pipeline viewer for a single document"` | `docs/viewer.html:25` | Der Nutzer sieht ein Dokument und bedient einen Viewer. Der Satz beschreibt die Seite jemandem, der nicht auf ihr ist |
| `"Facsimile"` | `docs/viewer.html:110` | Benennt ein Seitenbild als Seitenbild. Wird von keinem JS je überschrieben, steht also dauerhaft |
| `"TEI · rendered"` | `docs/assets/js/viewer.js:1335` | Wiederholt die im selben Header gedrückte Schaltfläche `"Rendered"` |
| Dreifachmarkierung Download | `docs/viewer.html:52-58` | Die Schaltfläche heißt `"Export"`, das Menülabel sagt `"(download)"`, und jeder der vier Einträge trägt zusätzlich `&darr;` |
| `"Transcription"` | `docs/viewer.html:133` | Wird bei jedem Render durch `textPanelTitle()` ersetzt und ist nur vor dem ersten Laden sichtbar |

Der Titel `"OCR · mistral"` (`docs/assets/js/viewer.js:1341`) ist ein Grenzfall. Der linke Teil wiederholt
die gedrückte Schaltfläche `"OCR"`, der rechte nennt die Engine und ist die einzige neue Information. Als
`"mistral"` allein bliebe der Informationsgehalt erhalten.

## 5. Wo die Umsetzung gegen das eigene System arbeitet

### 5.1 Zwei Rahmenstärken in einer Bedienzeile

`.btn` und `.input` nehmen `--h-border-emphasis` mit Alpha 0,25 (`docs/assets/css/base.css:72` Deklaration
77, `:128` Deklaration 129). `.panel__edit-toggle`, `.status-pill` und `.identity-chip` nehmen `--h-border`
mit Alpha 0,12 (`docs/assets/css/viewer.css:311`, `:102`, `:988`). Im Faksimile-Header stehen beide
Gruppen unmittelbar nebeneinander, zwei `.btn` für die Seitennavigation neben `"Edit layout"` als
`.panel__edit-toggle`. Gleichrangige Schalter erscheinen damit unterschiedlich schwer, ohne dass ein
Rangunterschied gemeint ist.

### 5.2 Zwei konkurrierende Sprachen für den gedrückten Zustand

`.btn[aria-pressed="true"]` färbt Fläche, Rahmen und Schrift ziegelrot (`docs/assets/css/base.css:121`).
`.panel__edit-toggle[aria-pressed="true"]` und `.mode-btn[aria-pressed="true"]` färben die Fläche anthrazit
mit inverser Schrift (`docs/assets/css/viewer.css:311` und `:204` jeweils nachfolgend). Der Viewer nutzt
die zweite Variante, die Basisschicht hält die erste vor. Für den Nutzer heißt Aktivsein damit je nach
Komponente etwas anderes, und die ziegelrote Variante steht als abweichendes Muster bereit.

### 5.3 Ein Token, das seinen Wert kopiert statt ihn zu referenzieren

`--h-filter: #8A8279` (`docs/assets/css/tokens.css:47`) ist zeichengleich mit `--h-text-muted: #8A8279`
(`:32`). Die vier Nachbarn `--h-heading`, `--h-paragraph`, `--h-footnote` und `--h-caption` (`:43-46`)
referenzieren sauber per `var()`. Der Ausreißer bricht die Ableitungskette im Katalog selbst.

### 5.4 Fremde Chrome im Faksimile-Panel

OpenSeadragon zeichnet eigene Bedienelemente mit Zoom, Home und Rotation
(`docs/assets/js/viewer.js:1207` und Umgebung), verankert oben links im Panel
(`docs/assets/js/viewer.js:1217`). Deren Sprite-Grafiken kommen vom CDN und folgen keinem `--h-*`-Token. In
der linken oberen Ecke des Faksimile-Panels steht damit die einzige Bedienelementgruppe der Anwendung, die
nicht aus dem Hersch-System stammt. Aus dem Code erschlossen, Sichtprüfung nötig.

### 5.5 Vertikales Budget in einer Shell mit fester Höhe

`.viewer-body` setzt `height: 100vh` mit `overflow: hidden` (`docs/assets/css/viewer.css:7` nachfolgend).
In dieser Spalte liegt der Footer, der über `.site-footer` zusätzlich `margin-top: var(--h-space-2xl)`
mitbringt (`docs/assets/css/base.css:322`, Deklaration 324), also 48 Pixel Leerraum über einer Zeile mit
Impressumslink und Repo-Symbol. Zusammen mit der Footerhöhe gehen daraus rund 100 Pixel an Panelhöhe
verloren. Gleichzeitig fordern `.panel__body--canvas` und `.facsimile-osd` je `min-height: 60vh`. Die
Überschlagsrechnung ergibt, dass sich beides bei Fensterhöhen unterhalb von etwa 750 Pixeln in die Quere
kommt. Erschlossen aus dem Code, Sichtprüfung bei kleiner Fensterhöhe nötig.

### 5.6 Totes CSS

`.toolbar__group` (`docs/assets/css/viewer.css:172`) wird nirgends erzeugt, das Markup nutzt durchgehend
`.editor-toolbar__group`. `.export-menu__sep` (`:1054`) wird ebenfalls nirgends erzeugt. Beides sind
Strukturangebote, die die Datei größer wirken lassen, als die Oberfläche ist.

## 6. Rangliste

### 6.1 Quick Wins, sicher und klein

Q1. Layout-Overlays im Lesemodus abschaltbar machen. Wirkung auf die häufigste Aufgabe am größten.
Die minimalste Fassung ist ein Schalter im Faksimile-Header, der eine Klasse auf dem OSD-Container umlegt,
gegen die `.region { display: none }` greift; Ausgangszustand aus. Belege `docs/assets/js/viewer.js:1225`,
`docs/assets/css/viewer.css:431`. Risiko gering, der Regionszähler in `.panel__hint` bleibt als Beleg
sichtbar, dass Layoutdaten vorliegen. Als Nebenwirkung muss der Layout-Editiermodus die Overlays unbedingt
zeigen, die Umschaltung darf dort nicht greifen.

Q2. Untertitel `"Pipeline viewer for a single document"` entfernen. Beleg `docs/viewer.html:25`. Kein
Risiko. `.site-header__center` behält den Badge und zentriert ihn.

Q3. Export-Tooltip auf die tatsächliche Funktion korrigieren. Beleg `docs/viewer.html:52`. Sachlicher
Fehler, das Menü bietet kein Verbinden an. Risiko null.

Q4. Sprachmischung im Entity-Popover und in der Legende vereinheitlichen. Belege
`docs/assets/js/viewer.js:579` gegen `:619`, dazu `:1586` und `:522`. Eine Sprache pro Oberfläche. Risiko
gering, betrifft nur Anzeigetexte. Als Nebenwirkung ist die Wahl der Sprache eine Festlegung, die restliche
Oberfläche ist englisch.

Q5. Dreifachmarkierung im Export-Menü auf eine Markierung reduzieren. Menülabel `"Single export (download)"`
streichen, die vier `&darr;` streichen, Schaltfläche `"Export"` behalten. Belege `docs/viewer.html:52-58`.
Risiko null.

Q6. Panel-Titel `"Facsimile"` streichen und den Titel des Textpanels auf den informationstragenden Rest
kürzen. Belege `docs/viewer.html:110`, `docs/assets/js/viewer.js:1335` und `:1341`. Risiko gering.
Als Nebenwirkung bleibt `#text-panel-title` als Element erhalten, weil JS darauf schreibt.

Q7. Footer-Abstand im Viewer neutralisieren. `margin-top` von `.site-footer` im Viewer-Kontext auf null
setzen, ohne `base.css` für die Prosaseiten zu verändern. Beleg `docs/assets/css/base.css:324`. Risiko
gering, gewinnt Panelhöhe.

Q8. Regionslisten-Überschrift kürzen. Beleg `docs/assets/js/layout-editor.js:465`. Bedienhinweis wandert in
ein `title`. Risiko null.

Q9. Rahmentoken in Bedienzeilen vereinheitlichen, also `.panel__edit-toggle` und `.btn` im selben Header
auf dasselbe Token bringen. Belege `docs/assets/css/base.css:77` gegen `docs/assets/css/viewer.css:313`.
Risiko gering. Die Änderung wirkt auch auf die Korpusseite und ist dort zu prüfen.

Q10. `--h-filter` auf `var(--h-text-muted)` umstellen und totes CSS entfernen. Belege
`docs/assets/css/tokens.css:47`, `docs/assets/css/viewer.css:172` und `:1054`. Risiko null, rein
redaktionell.

### 6.2 Strukturell, braucht eine Entscheidung

S1. Die zweite Subbar-Zeile auflösen. Die Trennlinie aus `docs/assets/css/viewer.css:76` verschwindet, die
Statuspills rücken an die Speichergruppe, wodurch der Hinweis `"Unsaved status · Save"` überflüssig wird.
Zu entscheiden ist, wohin die Layout-Werkzeugleiste geht, die derzeit dieselbe Zeile mitbenutzt. Ein
plausibler Weg legt sie in den Faksimile-Panel-Header, wo sie inhaltlich hingehört. Belege
`docs/viewer.html:63-99`, `docs/assets/css/viewer.css:75` und `:234-239`.

S2. Die Panel-Auszeichnung auf ein Mittel reduzieren. Derzeit markieren Rahmen, Radius, Schatten,
Header-Unterkante und drei Flächentöne dieselbe Grenze. Zu entscheiden ist, welches Mittel bleibt; der
Flächenton allein trägt die Trennung, weil `.panels` bereits eine Rinne setzt. Belege
`docs/assets/css/viewer.css:263`, `:272-278`, `:285`, `:344`. Die Änderung greift sichtbar in das
Erscheinungsbild ein und sollte am laufenden Viewer beurteilt werden.

S3. Die Legende im Entity-Modus auf die Prüfaufgabe beschneiden. Bis zu elf Chips stehen über dem Text, vier
davon gehören zur Aufgabe. Zu entscheiden ist, ob die Markup-Chips im Entity-Modus ganz entfallen oder
hinter eine Umschaltung wandern. Belege `docs/assets/js/viewer.js:1588-1595` und `:1620`.

S4. Entscheidungsgeste für Entitätskandidaten. Der Layer ist bewusst lesend, die Aufgabe verlangt aber ein
Urteil. Zu entscheiden ist, ob das Werkzeug ein Urteil aufnimmt, etwa als lokal gehaltene Markierung
analog zum Manifest, oder ob die Oberfläche den Weg zum externen Adjudikationspfad ausdrücklich benennt.
Belege `docs/assets/js/viewer.js:89` und der lesende Pfad in `renderTextPanel`.

S5. OSD-Bedienelemente durch eigene ersetzen. `showZoomControl` und Verwandte abschalten und drei eigene
Schaltflächen im Panel-Header setzen, die die vorhandene Viewport-API rufen. Ohne neue Abhängigkeit
machbar. Belege `docs/assets/js/viewer.js:1207` und `:1217`. Zu entscheiden ist, ob der Aufwand den
Konsistenzgewinn trägt.

S6. Tastaturbedienung sichtbar machen. Pfeiltasten sowie Home und End sind gebunden und nur in Tooltips
dokumentiert. Zu entscheiden ist der Ort, etwa eine unaufdringliche Zeile in der Fußzeile des
Faksimile-Panels.

### 6.3 Ausserhalb dieses Auftrags

A1. Statusvokabular `unverifiziert`, `in_arbeit`, `verifiziert`. Hängt am Datenmodell des Manifests und an
der Projektion in den `revisionDesc` bei der Übergabe. Änderungen brauchen die Abstimmung mit der
Bibliothek.

A2. Der Badge `"Experimental"` samt Tooltip. Trägt eine Aussage über den Prüfstatus der Inhalte und ist
keine gestalterische Frage.

A3. Footer-Inhalte mit Trägerschaft und Impressumslink. Institutionell und rechtlich gebunden.

A4. Eine durchgehende Sprachfestlegung für die gesamte Oberfläche. Der Einzelwiderspruch aus Q4 ist ein
Defekt und sofort behebbar; eine Gesamtumstellung ist eine Produktentscheidung.

A5. Dunkles Farbschema. Durch `color-scheme: light` in `docs/assets/css/tokens.css:92` und die
Projektvorgabe ausgeschlossen.

## 7. Verifikation

Geprüft wurde jede Fundstelle gegen den Plattenstand am 2026-08-12. Die Zeilennummern in `viewer.html`,
`base.css`, `tokens.css` und `layout-editor.js` wurden per `sed` einzeln aufgelöst und stimmen. Die
Selektorzeilen in `viewer.css` und die String-Fundstellen in `viewer.js` wurden per `grep` gegen den
aktuellen Stand neu aufgelöst, nachdem sich zeigte, dass parallele Instanzen `viewer.js`, `tei-render.js`
und `viewer.css` unversioniert verändern. Für diese drei Dateien gilt die Zeilennummer als Momentaufnahme,
der zitierte Selektor beziehungsweise String bleibt maßgeblich.

Nicht geprüft wurde die gerenderte Oberfläche. Kein Server wurde bedient, kein Screenshot erstellt. Die
Befunde 3.3 zum Zeilenumbruch der Statuszeile, 5.4 zu den OSD-Bedienelementen und 5.5 zum vertikalen Budget
sind aus dem Code erschlossen und brauchen je eine Sichtprüfung.

Der Arbeitsbaum trug zu Beginn und am Ende dieser Analyse fremde Änderungen paralleler Instanzen in
`knowledge/arbeitsbericht-v3.md`, `knowledge/journal.md`, `reports/2026-08-12_workflow-entitaetsannotation.md`
sowie in den drei genannten `docs/`-Dateien. Diese Analyse hat davon nichts angefasst. Die einzige von ihr
erzeugte Änderung ist diese Datei.
