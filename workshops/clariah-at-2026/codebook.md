# Codebuch für den Hersch-Pilotausschnitt

## Forschungsfrage

`How does Jeanne Hersch define the institutional conditions under which schools can foster critical judgement?`

Das Codebuch operationalisiert diese Frage für Dokument `1000`, Seiten `1000_p003` und `1000_p004`. Es wird ausschließlich in Prompt 04 verwendet. Die offene Baseline in Prompt 02 und der generische Schema-Lauf in Prompt 03 erhalten dieses Dokument nicht.

## Segment und Kodiereinheit

Der zulässige Text beginnt mit `L'ÉCOLE, LIEU DE RENCONTRE DE MÉMOIRE ET D'INVENTION` auf p003 und endet unmittelbar vor `POURQUOI IVAN ILLICH VEUT-IL DÉSCOLARISER LA SOCIÉTÉ ?` auf p004.

Eine Themenannotation formuliert einen analytisch eigenständigen Claim und verbindet ihn mit mindestens einem exakten Zitat. Ein Code darf mehrfach auftreten. Ein Zitat darf mehrere Codes stützen, wenn die Claims getrennt und jeweils nachvollziehbar sind.

## Statusregeln

- `direct`: Der Wortlaut belegt den Claim explizit.
- `indirect`: Der Claim entsteht durch eine nachvollziehbare Synthese oder Interpretation mehrerer Textsignale.
- `ambiguous`: Konkurrierende Lesarten oder noch unzureichende Textsignale verhindern eine eindeutige Zuordnung.
- `unchecked`: Die für `source_checked` erforderliche menschliche Prüfung von Zitat und Seitenanker liegt nicht vor. Agentische, visuelle oder automatisierte Vorprüfungen ändern diesen Status nicht. Jeder Modelloutput startet hier.
- `source_checked`: Ein Mensch hat Zitat, Seite und Segmentgrenze geprüft.
- `source_mismatch`: Zitat oder Seitenanker stimmt nicht mit der Quelle überein.
- `unreviewed`: Es liegt noch keine fachliche Entscheidung vor. Jeder Modelloutput startet hier.
- `accepted` und `rejected`: fachliche Annahme oder Ablehnung nach einem dokumentierten menschlichen Source-Check. Beide Werte sind nur zusammen mit `source_check_status: source_checked` zulässig. Bei `unchecked` oder `source_mismatch` bleibt `review_status: unreviewed`.

Entity-Kennungen werden nur vergeben, wenn eine kontrollierte Quelle die Identität trägt. Ohne geprüfte Kennung bleiben `identifier` und `identifier_source` null.

## `school_as_encounter`

### Definition

Schule und Klasse erscheinen als institutionell geschützte Begegnungsräume. Mehrfache Zugehörigkeiten, Vielfalt der Personen und die gemeinsame Ausrichtung auf einen Gegenstand ermöglichen Distanz, Zuhören und kritisches Fragen.

### Einschließen

- Schule als Gegenüber, Ergänzung oder Ersatz der Familie
- gemeinsame Erinnerungen und mehrere Zugehörigkeiten
- Vielfalt von Kindern und Lehrpersonen
- gemeinsame Konzentration von Lehrperson und Kind auf einen bestimmten Gegenstand
- Respekt und Zuhören als Form der Infragestellung

### Ausschließen

- allgemeine Verteidigung der Schule ohne Begegnungsdimension
- Gedächtnisinhalte als Material des Urteilens
- politische Neutralität als institutionelle Grenze

### Anker

`La classe est un lieu de rencontre, l'« autre » de la famille, son substitut parfois, son complément toujours.` auf `1000_p004`.

## `memory_for_judgement`

### Definition

Gedächtnis, Inhalte und historisch-kulturelle Erfahrung schaffen das Vergleichsmaterial, das Denken, Distanz und kritisches Urteil benötigen.

### Einschließen

- erinnerte Inhalte als Voraussetzung des Kritisierens
- Bücher als Erweiterung der Erfahrung
- Vergangenheit als Vergleichsraum
- Distanz durch Fächer, Texte, Epochen und Persönlichkeiten

### Ausschließen

- gemeinsame Erinnerungen, wenn ihre soziale Zugehörigkeitsfunktion im Zentrum steht
- Wissensakkumulation ohne Bezug auf Vergleich, Kritik oder Urteil

### Anker

`On ne peut critiquer qu'avec des contenus de mémoire.` auf `1000_p004`.

## `pedagogical_invention`

### Definition

Pädagogische Praxis wird als gestaltbare institutionelle Tätigkeit beschrieben. Formen des Klassenlebens, Wahrnehmung, Diskussion und die Behandlung großer Probleme werden bewusst eingerichtet.

### Einschließen

- Erfindung und Verbesserung von Formen des Klassenlebens
- Schulung des Sehens und Hörens
- Behandlung von Frieden, Gerechtigkeit und Freiheit im Unterricht
- Diskussion und Austausch über Kontakte mit der Außenwelt
- Suche nach einem passenden Bildungsweg

### Ausschließen

- Reformforderungen ohne konkrete Gestaltungsdimension
- politische Propaganda

### Anker

`Il s'agit d'inventer les formes de la vie en classe, de trouver les procédés qui l'améliorent dans le cadre de ce qui est compatible.` auf `1000_p004`.

## `social_compensation`

### Definition

Schule soll soziale Ausgangsunterschiede teilweise ausgleichen, ergänzende Beziehungen eröffnen und gleiche Achtung bei ungleichen Fähigkeiten institutionell sichern.

### Einschließen

- ausdrücklicher Ausgleich sozialer Ungleichheit
- Gedächtnis als teilweise Kompensation ungleicher Herkunft
- Schule als Ersatz oder Ergänzung fehlender Beziehungen

### Ausschließen

- biologische Unterschiede, die der Text vom Ausgleich ausnimmt
- soziale Verantwortung ohne Kompensationsbezug

### Anker

`Et l'école a pour mission d'essayer de compenser les inégalités sociales — et non biologiques.` auf `1000_p004`.

## `political_neutrality`

### Definition

Politische Neutralität schützt die Schule als Raum kritischer Auseinandersetzung vor Propaganda. Politische Gegenstände können behandelt werden, sofern die Institution nicht zum Mittel politischer Einflussnahme wird.

### Einschließen

- Kritik am Vorwurf nur scheinbarer Neutralität
- staatliche Gewährleistung politischer Neutralität
- Abgrenzung von Propaganda
- Zusammenhang zwischen Neutralität und kritischem Denken

### Ausschließen

- Behandlung von Frieden, Gerechtigkeit oder Freiheit als Unterrichtsgegenständen
- Herrschafts- und Reproduktionskritik aus dem ausgeschlossenen Illich-Beitrag

### Anker

`Un grand danger réside dans la politisation de l'école.` und der folgende Satz zur staatlich garantierten Neutralität auf `1000_p004`.
