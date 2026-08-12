# Kontrollierte Entitätsannotation in OCR-basierten Editionsdaten

Kompaktes Arbeitspapier, Stand 2026-08-12. Es beschreibt den **Workflow**, mit dem im
Projekt zbz-ocr-tei Personen, Organisationen und Werke in den TEI-Daten des
Zeitungsausschnitt-Korpus zu Jeanne Hersch mit GND-Referenzen ausgezeichnet und die
Ergebnisse gemessen werden. Die operativen Details stehen in
[knowledge/entity-integration.md](../knowledge/entity-integration.md) und
[knowledge/entity-evaluation.md](../knowledge/entity-evaluation.md); die aktuellen
Messwerte hält der jeweils regenerierte Report des Werkzeugs, sie werden hier bewusst
nicht zitiert.

## Gegenstand und Grundsatz

Ausgangspunkt ist eine von der Zentralbibliothek Zürich kuratierte Entitätsliste, in
der jeder Eintrag eine GND-Kennung trägt. Der Workflow folgt dem **Closed-World-Prinzip**. Ausgezeichnet wird ausschließlich, was auf dieser Liste steht, und die
Zuordnung einer Kennung zu einer Textstelle trifft immer ein **deterministisches,
wiederholbares Verfahren**. Sprachmodelle sind von dieser Zuordnungsentscheidung
ausgeschlossen. Sie kommen an zwei eng begrenzten Stellen vor, als Prüfinstanz über bereits vorhandene Namensformen und
als geplante Vorsortierung einer Worklist; beide Ergebnisse werden in versionierten
Dateien festgehalten und anschließend deterministisch konsumiert, sodass jeder Lauf
ohne Modellbeteiligung reproduzierbar bleibt. Namen, die im Korpus häufig vorkommen,
aber auf der Liste fehlen, werden als **NIL-Mentions** ohne
Kennungsvergabe erfasst und als Kandidaten für die Listenerweiterung vorgelegt; die
Entscheidung über die Liste bleibt bei der Bibliothek.

## Namensformen und ihre Kontrolle

Zu jeder Kennung werden die in der Normdatenbank verzeichneten Namensvarianten über
die lobid-Schnittstelle in einen lokalen Cache geholt und um Formen aus dem
Altbestand des Projekts ergänzt. Rohe Normdaten-Varianten sind als Suchgrundlage
unzuverlässig, sie enthalten Initialenkürzel, Transliterationsfragmente und
Verwechslungsformen. Deshalb durchläuft jede übernommene Form eine Prüfung, deren
Ergebnis als **Verdict in einer versionierten Datei** liegt. Zugelassene Formen speisen
die Suche, verworfene Formen erreichen sie nie, und Formen mit Verdacht sowie alle
seit der letzten Prüfung neu hinzugekommenen Formen erzeugen ausschließlich
Prüflisten-Einträge. Die Datei ist durch die Projektleitung änderbar, und jede
Änderung wirkt beim nächsten Lauf.

## Zweistufige Annotation

Ein regelbasierter Matcher liest jede Lieferdatei und sortiert jeden Fund in eine von
**zwei Stufen**. Tier 1 umfasst als sicher geltende Treffer, etwa vollständige Namen
mit eindeutigem Träger; nur sie werden ausgezeichnet. Tier 2 umfasst alles
Unsichere, nackte Nachnamen, Stellen mit mehreren möglichen Trägern,
Homographenverdacht und ungeprüfte Namensformen; diese Stufe wird als **Worklist**
sichtbar gemacht und niemals automatisch ausgezeichnet. **Definierte Zonen** sind von der
Suche ausgenommen, darunter Bildnachweise, gekennzeichnete Literaturverzeichnisse und
die Verfasserzeilen der Autorin.

Die Auszeichnung erfolgt zunächst in Vorschaudateien, die Lieferdaten bleiben
unberührt. Jede Vorschau muss **zwei maschinell geprüfte Invarianten** erfüllen, die
Schema-Validität gegen das Projektschema und die Zeichenidentität des Textes vor und
nach der Auszeichnung. Ein Viewer zeigt Markierungen, Kandidaten samt Herkunft der
Namensform und die Prüfliste im Textzusammenhang; der Bearbeitungsstand jedes
Dokuments wird als **Workflow-Status von Menschen** gesetzt und überlebt alle Neuläufe.

## Stichprobenbasierte Evaluation

Der Vergleich mit den fünfundzwanzig handannotierten Referenz-TEIs der Bibliothek
dient als **Trendindikator**, taugt jedoch als Wahrheitsmaßstab nur eingeschränkt, weil
die Referenzen Teiltranskriptionen sind und intern uneinheitlich annotieren. Die
belastbare Messung folgt deshalb einem **Stichprobenprotokoll mit vier Eigenschaften**.

Erstens wird **reproduzierbar gezogen**, mit festem Seed und dokumentierter Schichtung.
Die Präzisionsfrage beantwortet eine Stichprobe von dreihundert Markierungen,
geschichtet nach Kategorie und Regelfamilie; die Vollständigkeitsfrage beantwortet
eine Stichprobe von vierzig vollständigen Seiten, geschichtet nach Layouttyp und
Sprache. Zweitens wird **am Faksimile
adjudiziert**. Jede gezogene Markierung erhält genau ein begründetes Urteil (korrekt,
falsche Entität, falsche Spanne, nicht in der Vorlage, unentscheidbar); jede gezogene
Seite wird erschöpfend gegen die Liste gelesen, und jede übersehene Nennung erhält
ein Ursachenlabel. Drittens wird eine Teilmenge von fünfzig Fällen **doppelt und
unabhängig beurteilt**, sodass die Verlässlichkeit des Urteilens selbst als
**Inter-Annotator-Agreement** ausgewiesen ist. Viertens werden die Kennzahlen mit
**Bootstrap-Konfidenzintervallen** berichtet, nach dem Verfahren, das im Projekt bereits
die Zeichenfehlerraten-Messung trägt.

Die Messung hat Konsequenzen über die Zahl hinaus. Jeder bestätigte Fehler wird als
**Regressionstest** fixiert, systematische Ursachen werden zu Matcher-Regeln,
Namensform-Verdicts oder Listenvorschlägen, und die Entscheidung, die Markierungen
in den Lieferbestand zu übernehmen, fällt **pro Kategorie auf Grundlage der gemessenen
Präzision**. Der Bestandslauf selbst folgt dem etablierten Muster der reversiblen
Korrekturläufe, mit Vorschau, Sicherungskopie und erneuter Validierung.

## Rollen und Grenzen

Agenten übernehmen Voradjudikation, erschöpfende Seitenlektüre und Statistikläufe.
Die Projektleitung kontrolliert Stichproben der Urteile, entscheidet strittige Fälle
und gibt Bestandseingriffe frei. Die Bibliothek entscheidet Spezifikationsfragen der
Annotationspraxis und die Erweiterung der Liste. Die Methode misst Korrektheit
**relativ zur kuratierten Liste** und zur dokumentierten Annotationsspezifikation;
Aussagen über nicht gelistete Entitäten trifft sie nicht. **Bekannte Grenzen** sind
dokumentiert, darunter die Abhängigkeit der Zonenregeln von korrekter
Strukturauszeichnung der Pipeline-TEI und Einzeldokumente mit defekter
Seitenzuordnung, die einer eigenen, freigabepflichtigen Reparatur vorbehalten sind.
