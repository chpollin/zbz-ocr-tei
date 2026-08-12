# Kontrollierte Entitätsannotation in OCR-basierten Editionsdaten

Kompaktes Arbeitspapier, Stand 2026-08-12. Es beschreibt den **Workflow**, mit dem im
Projekt zbz-ocr-tei Personen, Organisationen und Werke in den TEI-Daten des
Zeitungsausschnitt-Korpus zu Jeanne Hersch mit GND-Referenzen ausgezeichnet und die
Ergebnisse gemessen werden, und berichtet die Befunde des ausgeführten Experiments. Die
operativen Details stehen in
[knowledge/entity-integration.md](../knowledge/entity-integration.md) und
[knowledge/entity-evaluation.md](../knowledge/entity-evaluation.md). Zitierfähig sind in
einem datierten Arbeitspapier die eingefrorenen Ergebnisse eines Experiments, gebunden an
Seed, Snapshot-Datum und versionierte Verdict-Dateien; laufende Betriebskennzahlen bleiben
ausgeschlossen und stehen im jeweils regenerierten Report des Werkzeugs.

## Gegenstand und Grundsatz

Ausgangspunkt ist eine von der Zentralbibliothek Zürich kuratierte Entitätsliste, in der
jeder Eintrag eine GND-Kennung trägt. Der Workflow folgt dem
**Closed-World-Prinzip**. Ausgezeichnet wird ausschließlich, was auf dieser Liste steht,
und die Zuordnung einer Kennung zu einer Textstelle trifft immer ein **deterministisches,
wiederholbares Verfahren**. Sprachmodelle sind von dieser Entscheidung ausgeschlossen. Sie
kommen an zwei eng begrenzten Stellen vor, als Prüfinstanz über vorhandene Namensformen
und als Vorsortierung einer Worklist; beide Ergebnisse liegen in versionierten Dateien und
werden deterministisch konsumiert, sodass jeder Lauf reproduzierbar bleibt. Namen, die im
Korpus vorkommen und auf der Liste fehlen, werden als **NIL-Mentions** ohne
Kennungsvergabe erfasst und der Bibliothek als Kandidaten für die Listenerweiterung
vorgelegt.

## Namensformen und ihre Kontrolle

Zu jeder Kennung werden die in der Normdatenbank verzeichneten Namensvarianten über die
lobid-Schnittstelle in einen lokalen Cache geholt und um Formen aus dem Altbestand des
Projekts ergänzt. Rohe Normdaten-Varianten sind als Suchgrundlage unzuverlässig, sie
enthalten Initialenkürzel, Transliterationsfragmente und Verwechslungsformen. Deshalb
durchläuft jede übernommene Form eine Prüfung, deren Ergebnis als **Verdict in einer
versionierten Datei** liegt. Zugelassene Formen speisen die Suche, verworfene erreichen
sie nie, und Formen mit Verdacht wie auch alle neu hinzugekommenen erzeugen ausschließlich
Prüflisten-Einträge. Die Datei ist durch die Projektleitung änderbar, und jede Änderung wirkt
beim nächsten Lauf.

## Zweistufige Annotation

Ein regelbasierter Matcher liest jede Lieferdatei und sortiert jeden Fund in eine von
**zwei Stufen**. Tier 1 umfasst als sicher geltende Treffer, etwa vollständige Namen mit
eindeutigem Träger; nur sie werden ausgezeichnet. Tier 2 umfasst alles Unsichere, nackte
Nachnamen, mehrdeutige Träger, Homographenverdacht und ungeprüfte Namensformen; diese
Stufe wird als **Worklist** sichtbar gemacht und niemals automatisch ausgezeichnet.
**Definierte Zonen** sind von der Suche ausgenommen, darunter Bildnachweise,
gekennzeichnete Literaturverzeichnisse und die Verfasserzeilen der Autorin. Im
**Paratext** einer Seite gilt der Konventionsentscheid vom 2026-08-12; Kolumnentitel
bleiben unmarkiert, während Titelblätter, Organisationsnamen in Verfasserzeilen und
Bildlegenden ausgezeichnet werden (Entscheidungsregister E105 in
[knowledge/decisions.md](../knowledge/decisions.md)).

Die Auszeichnung erfolgt zunächst in Vorschaudateien, die Lieferdaten bleiben unberührt.
Jede Vorschau muss **drei maschinell geprüfte Invarianten** erfüllen, die Schema-Validität
gegen das Projektschema, die Zeichenidentität des Textes vor und nach der Auszeichnung und
die Mitgliedschaft jeder vergebenen Kennung in der kuratierten Liste; die dritte prüft ein
Test-Gate durch exakten Stringvergleich über alle ausgelieferten Artefakte. Ein Viewer
zeigt Markierungen, Kandidaten samt Herkunft der Namensform und die Prüfliste im
Textzusammenhang; den Bearbeitungsstand setzt ein Mensch als **Workflow-Status**, der alle
Neuläufe überlebt.

## Persistenz der Urteile

Jedes am Faksimile gefällte Urteil liegt in einem **versionierten Verdict-Store**,
geschlüsselt nach Dokument, Seite, Oberflächenform, Kennung und Vorkommen und pro Dokument
an eine sha256-Prüfsumme des Quelltextes gebunden. Der Schlüssel führt keine
Zeichenoffsets, deshalb macht eine spätere Textänderung wie eine Neu-OCR oder ein
Bestandskorrekturlauf die betroffenen Datensätze als veraltet sichtbar und stellt sie zur
erneuten Adjudikation, während der übrige Bestand gültig bleibt. Geprüftes Wissen kumuliert
so über Läufe hinweg und geht als Eingabe in jede spätere Messung ein (E106).

## Stichprobenbasierte Evaluation

Der Vergleich mit den fünfundzwanzig handannotierten Referenz-TEIs der Bibliothek
dient als **Trendindikator**, taugt jedoch als Wahrheitsmaßstab nur eingeschränkt, weil
die Referenzen Teiltranskriptionen sind und intern uneinheitlich annotieren. Die
belastbare Messung folgt deshalb einem **Stichprobenprotokoll mit vier Eigenschaften**.

Erstens wird **reproduzierbar gezogen**, mit festem Seed und dokumentierter Schichtung
nach Kategorie und Regelfamilie für die Markierungen, nach Layouttyp und Sprache für die
Seiten. Zweitens wird **am Faksimile adjudiziert**, mit genau einem begründeten Urteil je
gezogener Markierung, erschöpfender Lektüre je gezogener Seite und einem Ursachenlabel je
übersehener Nennung. Drittens beurteilt eine zweite, unabhängige Instanz eine Teilmenge
blind, sodass die Verlässlichkeit des Urteilens selbst als **Inter-Annotator-Agreement**
ausgewiesen ist. Viertens werden die Kennzahlen mit **Bootstrap-Konfidenzintervallen**
berichtet, nach dem Verfahren der Zeichenfehlerraten-Messung im Projekt.

## Befunde

Der ausgeführte Lauf hat das Snapshot-Datum 2026-08-12. Die **Präzision** der automatisch
gesetzten Markierungen liegt bei 279 von 293 entscheidbaren Fällen und damit bei 0,952,
mit einem Bootstrap-Konfidenzintervall von 0,925 bis 0,976 bei Seed 42. Unentscheidbar
blieben 7 der 300 gezogenen Fälle, weil zwei Dokumente eine defekte Seitenzuordnung haben.
Die blind doppelt beurteilte Teilmenge stimmt in 48 von 50 Fällen überein.

Die **Vollständigkeit** misst die erschöpfende Lektüre von 40 Seiten mit 67 Nennungen
gelisteter Entitäten. Davon sind 20 automatisch ausgezeichnet und 17 auf der Worklist
sichtbar, 30 bleiben übersehen. Die Ursachen sind 28 Regellücken und 2 Lexikonlücken; die
OCR-Qualität verursacht keine einzige Auslassung. Die Belege je Fall stehen im
Ergebnisbericht
[reports/2026-08-12_entity-eval-ergebnis.md](2026-08-12_entity-eval-ergebnis.md).

## Konsequenzen der Messung

Die benannten Regellücken sind in **fünf deterministische Reparaturen** übersetzt,
Kleinschreibungstoleranz für Akronyme, Abstreifen des Klammerqualifikators einer
GND-Ansetzung, Inversion adjektivischer Ortsformen, Wortgrenze vor hochgestellter
Fußnotenziffer und Behandlung von Personeninitialen. Alle fünf erzeugen ausschließlich
Worklist-Vorschläge, weil eine abgeleitete Namensform eine Vermutung über einen Namen ist
und erst nach menschlicher Prüfung in den Lieferbestand gelangt (E106).

Gegen denselben eingefrorenen Korpus-Scan gerechnet, wächst die Worklist dadurch um rund
1650 Vorschläge, während sich die automatischen Markierungen um 9 gewonnene Treffer an
hochgestellten Fußnotenziffern und eine entfernte Markierung im Inneren eines Kompositums
verschieben. Das ist der empirische Nachweis, dass **Messen in einem deterministischen
System klassenweise wirkt**. Ein adjudizierter Einzelfall wird zur Regelklasse, deren
Wirkung auf den gesamten Korpus vor dem Übernahmeentscheid beziffert ist.

Jeder bestätigte Fehler wird als **Regressionstest** fixiert, und die Übernahme in den
Lieferbestand entscheidet sich pro Kategorie an der gemessenen Präzision, im Muster der
reversiblen Korrekturläufe mit Vorschau, Sicherungskopie und erneuter Validierung. Die
Prüfung des Gesamtbestands läuft risikogeordnet weiter, ein deterministisches Ranking
sortiert die automatischen Markierungen nach Fehlerwahrscheinlichkeit und die Adjudikation
beginnt am oberen Ende, was die Methode jenseits der Stichprobe ökonomisch hält.

## Fallstudie Paratext

Vier am Faksimile entschiedene Fälle begründen die **Paratext-Konvention**. In Dokument
330 steht der eigene Titel des Buches als Kopfzeile über jeder Seite und wurde in der
Stichprobe sechzehnmal identisch ausgezeichnet; solche Wiederholungen bleiben seither unmarkiert,
weil jede genau die Angabe führt, die die vorige schon geführt hat. Das Titelblatt einer
Dissertation in Dokument 110 nennt die Universität, die Verfasserzeile in Dokument 500 die
Hochschulzugehörigkeit und eine Bildlegende in Dokument 760 das besitzende Museum eines
Ausstellungskatalogs; diese drei Klassen werden ausgezeichnet, weil jede eine Angabe mit
Forschungswert trägt (E105).

Weil die Urteile pro Nennung persistiert sind, ist die **Konventionslesart** ohne neue
Ziehung rechenbar. Die 25 gezogenen Markierungen, deren Adjudikationsbegründung einen
Kolumnentitel nennt, sind sämtlich als korrekt beurteilt; ohne sie steht die Präzision bei
254 von 268 entscheidbaren Fällen und damit bei 0,948. Die Kennzahl verändert sich damit
kaum, und der redundante Anteil des ausgezeichneten Bestands entfällt.

## Drei Arten von Wissen

Die Methode trennt drei Arten von Wissen. **Erschöpfend geprüfte Invarianten** gelten für
den gesamten Bestand, etwa der Nachweis, dass jede vergebene Kennung Mitglied der
kuratierten Liste ist, den ein Test-Gate über alle ausgelieferten Artefakte führt.
**Verifiziertes Einzelwissen** gilt für die adjudizierten Fälle, und die Verlässlichkeit
des Urteilens selbst ist durch die Doppelbeurteilung beziffert. **Statistische Inferenz**
schließt von der Stichprobe auf den Korpus und wird nur mit Konfidenzintervall berichtet.
Unsicher ist allein die dritte Art, und jede zusätzlich pro Nennung verifizierte
Markierung überführt einen Teil davon in die zweite.

## Rollen und Grenzen

Agenten übernehmen Voradjudikation, erschöpfende Seitenlektüre und Statistikläufe. Der
Selbstbericht eines Agenten gilt als ungeprüft, bis er gegen den tatsächlichen
Dateizustand kontrolliert ist; die Orchestrierung führt die entscheidenden Prüfungen
selbst nach ([knowledge/agent-orchestration.md](../knowledge/agent-orchestration.md)).
Die Projektleitung kontrolliert Stichproben der Urteile, entscheidet strittige Fälle
und gibt Bestandseingriffe frei. Die Bibliothek entscheidet Spezifikationsfragen der
Annotationspraxis und die Erweiterung der Liste. Die Methode misst Korrektheit
**relativ zur kuratierten Liste** und zur dokumentierten Annotationsspezifikation;
Aussagen über nicht gelistete Entitäten trifft sie nicht. **Bekannte Grenzen** sind
dokumentiert, darunter die Abhängigkeit der Zonenregeln von korrekter
Strukturauszeichnung der Pipeline-TEI und Einzeldokumente mit defekter
Seitenzuordnung, die einer eigenen, freigabepflichtigen Reparatur vorbehalten sind.
