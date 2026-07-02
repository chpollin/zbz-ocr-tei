# Unabhängige CER-Gegenprobe (2026-07-03)

Externe Verifikation der Fidelity-CER-Headline (Mean 2,71 % / Median 1,40 %, n=25) im Zuge der Arbeit am kanonischen Promptotyping-Paper. Anlass war die Operator-Frage, ob die Zahlen solide sind. Die Gegenprobe wurde ohne jeden Import von Repo-Code durchgeführt; Extraktion und Normalisierung wurden aus der dokumentierten Spezifikation neu implementiert (stdlib ElementTree, eigene Regexes), die Distanzen kommen aus python-Levenshtein 0.27.3 als zweiter C-Engine neben rapidfuzz, Aggregation und Statistik sind eigener Code. Skripte: `gegenprobe_cer.py`, `gegenprobe_metrics.py` im Verifikationsordner des Paper-Repos (`DHCraft/promptotyping-paper/verification/`). Das Repo blieb unangetastet (read-only).

## 1. Arithmetik: vollständig bestätigt

Alle dokumentierten Werte reproduzieren auf die Dezimale: Fidelity 2,71 %/1,40 %, micro 2,13 %, Volltext 18,94 %/12,13 %, Scope 16,23 %/7,06 %, die Einzelwerte der sechs korrigierten Docs (30, 290, 1910, 90, 40, 1520) exakt, ebenso die Vorher-Vektoren 3,99 %/1,83 % und 4,26 %/1,83 %. Beide Engines liefern auf allen 25 Distanzen identische Werte; die Fidelity/Scope-Zerlegung ist auf den 15 speicherseitig kreuz-alignierbaren Docs alignment-stabil (Delta 0,0000 pp). Da die Extraktion aus der Spezifikation neu geschrieben wurde und trotzdem exakt trifft, beschreibt `quality.md` das tatsächliche Verhalten von `evaluate_ocr.py` korrekt.

**Schwellen-Sensitivität.** Die Headline hängt an `SCOPE_BLOCK_MIN = 50`:

| Schwelle | Mean | Median |
|---|---|---|
| 30 | 2,38 % | 1,21 % |
| **50 (Headline)** | **2,71 %** | **1,40 %** |
| 100 | 3,33 % | 2,10 % |

Beim Zitieren der Zahl gehört die 50-Zeichen-Schwelle genannt.

## 2. Zweitmetriken (n=25, unabhängig gerechnet)

| Metrik | Mean | Median | misst |
|---|---|---|---|
| Fidelity-CER (Kontrolle) | 2,71 % | 1,40 % | wie Headline |
| WER total (scope-inkl.) | 22,98 % | 14,19 % | Wortebene, volle Divergenz |
| CER case-insensitiv total | 18,87 % | 11,98 % | Case-Anteil an der Volltext-Divergenz |
| Bag-of-chars-Miss | 0,36 % | **0,01 %** | echt fehlende Referenzzeichen, alignmentfrei |
| Bag-of-words-Recall | 94,78 % | 95,50 % | formgleich wiedergefundene Referenzwörter |

Die Triangulation ist kohärent. Der alignmentfreie Bag-of-chars-Miss zeigt, dass vom Referenztext im Median praktisch nichts fehlt; die Fidelity-CER besteht überwiegend aus Substitutionen und kleinen Einfügungen. Ein Word-Recall von ~95 % passt rechnerisch zu ~1,4 % Zeichenfehlern (ein Zeichenfehler berührt ein ganzes Wort). WER und CER-total bestätigen nur das bekannte Scope-Phänomen der selektiven Referenzen (Extremfall Doc 570 mit Volltext-CER 113 % bei Scope 112 %).

## 3. Inhaltlicher Durchgang: alle 25 Docs, Top-Fehlerblöcke klassifiziert

Für jedes der 25 Dokumente wurden die sechs größten Fidelity-Blöcke inhaltlich geprüft (Dump regenerierbar über `gegenprobe_metrics.py`). Vier Fehlerklassen tragen die Headline:

**a) Seitenapparat-Einfügungen unter 50 Zeichen (häufigste Klasse, kein Erkennungsfehler).** Kolumnentitel, Seitenzahlen, Impressum, Copyright, Katalogmetadaten, Sprecherlabels, die die Pipeline transkribiert und die selektive Referenz weglässt: „TEMPS ALTERNÉS 153" (Doc 40), „LE PROBLÈME DE L'ÉLITE OUVRIÈRE" (130), „SLZ 51/52, 17. Dezember 1970" (890), „JASPERS" (3040), „JEANNE HERSCH" (100, 560, 2530, 3020), Bibliotheksvermerke (300), Inhaltsverzeichnis-Fragmente (90). Diese Klasse erklärt die Schwellen-Sensitivität aus §1 und bedeutet, dass die Fidelity-CER die reine Erkennungsleistung auch aus diesem Grund überschätzt (zusätzlich zur bekannten Referenz-Fehlbarkeit).

**b) Echter Textverlust (die eigentlich relevanten Fälle).**
- **Doc 30** (11,59 %, char_miss 6,87 %): drei Blöcke à 540/449/194 Zeichen fehlen. Am Faksimile visuell verifiziert: Das PDF ist ein aufgeschlagenes Buch als Doppelseite, der gesamte fehlende Text steht auf der linken Seite. Wurzelursache ist die Doppelseiten-Fotografie, kein OCR-Zeichenproblem. Kandidat für gezielte Nachbearbeitung.
- **Doc 1910** (7,69 %): mehrere fehlende deutsche Passagen (199/71/38/26/26 Zeichen) im Umfeld von Fachbegriffserläuterungen.
- **Doc 1520** (2,11 %): systematisches Muster, fehlende eingeklammerte Quellenangaben wie „(Introduction à la philosophie, trad. française 1re édition p. 55-57)"; sechs der Top-Blöcke sind sämtlich solche Zitatnachweise.
- **Doc 760** (5,87 %): fehlende Bildlegenden im Kunstkatalog („Le Cirque - l'écuyère" 1957, 150,5 x 100 …).
- **Doc 1180** (1,12 %): ein fehlender Satz (~150 Zeichen, zusammenhängend).
- **Doc 2635** (0,76 %): eine Bildlegende plus eine getilgte Wortwiederholung („und Schichten").

**c) Konventionsdivergenzen zulasten der Referenz.** Am Faksimile von Doc 100 visuell verifiziert: Der Druck zeigt „UNE PHILOSOPHIE DE L'EXISTENCE: KARL JASPERS" in Versalien, die Pipeline transkribiert versalientreu, die Transkribus-Referenz normalisiert auf Kleinschreibung; die case-sensitiven „Fehler" messen hier Referenzkonvention, nicht Erkennung (gleiche Signatur in Doc 2635 und 3040). Verwandt: Akzent-Setzung auf Großbuchstaben (Doc 2530, A↔À, E↔É) und die Ellipse U+2026 gegen drei Punkte (Doc 570), die die symmetrische Normalisierung derzeit nicht abfängt.

**d) Echte Zeichen-Fehlerkennungen.** In den Top-Blöcken selten: Einzelzeichen-Substitutionen (Doc 1060 u↔i, Doc 830 ô↔à, Trennstrich-Reste), eine verstümmelte Zeile (Doc 2310).

## 4. Konsequenzen

1. Die Headline 2,71 %/1,40 % ist arithmetisch korrekt, reproduzierbar und als **Obergrenze** der Erkennungsfehlerrate doppelt abgesichert (fehlbare Referenz, Apparat-Einfügungen). Die tatsächliche Zeichen-Erkennungsleistung liegt darunter.
2. Zitierform überall mit n=25, Schwelle 50 und Stand 2026-06-08.
3. Mögliche Folgearbeiten (Entscheidung liegt beim Projekt, nicht hier getroffen): Ellipsen-Normalisierung (U+2026 ↔ „...") symmetrisch ergänzen; Apparat-Einfügungen als eigene Kategorie ausweisen, falls eine reine Erkennungsrate gewünscht ist; Doc 30 wegen der Doppelseiten-Ursache gezielt nachziehen; die Versalien-Konventionsdivergenz der Referenz in `quality.md` bei der Referenz-Fehlbarkeit mit dokumentieren.

**Grenze der Aussage.** Ground Truth existiert nur für diese 25 Dokumente. Für die übrigen ~260 Dokumente des Korpus ist keine CER messbar; dort gelten weiterhin nur die dokumentierten Proxys (Schema-Validität, Layout-QA, Wörterbuch-Plausibilitätsband).
