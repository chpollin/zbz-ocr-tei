# Entity-Evaluation, Ergebnis des Snapshots 2026-08-12

Methode: knowledge/entity-evaluation.md; Protokoll: reports/2026-08-12_adjudication-protokoll.md;
Rohdaten: output/audits/eval_sample/ (Manifest, Fall-Dateien, 9 Verdict-Dateien),
aggregiert in output/audits/entity_eval_report.json. Alle Urteile faksimile-adjudiziert
durch 9 unabhaengige Agenten; jede Datei gegen die Vorgabe verifiziert.

## Gemessen (Praezision, Tier 1)

300 gezogene Markierungen: 279 correct, 5 wrong_entity, 4 wrong_span, 5 not_in_source,
7 undecidable (Seitenzuordnungs-Defekte Dok 120/1350). Praezision nach Protokoll-Lesart
ueber 293 entscheidbare Faelle: 0.952, Bootstrap-95%-Intervall (Perzentil, Seed 42):
0.925 bis 0.976. Inter-Annotator-Agreement (50 Faelle, blind doppelt): 48/50 = 0.96;
beide Abweichungen (p145 Geisterbild-Durchdruck, p193 Name im Titelslot) sind
dokumentiert und gehen an den Operator.

## Beschrieben (nicht gemessen)

Seitenapparat-Konvention offen: nach Stichwort-Heuristik sitzen 56 der 279 correct in
Kolumnentiteln, Titelblaettern, Bylines (allein 16x derselbe Kolumnentitel in Dok 330);
Lesart ohne Seitenapparat ist erst nach Konventionsentscheid berechenbar. Fehlerklassen:
Werk/Person-Verwechslung in Bibliographie-Slots (Augustin-Roman, Schilpp-/Salamun-Titel),
UNESCO-Kommission-Kompositum (Bindestrich-Guard fehlt), kurze Werkvariante trifft
Gattungswort (Die Mauer), Split-Wrap Saint Ignace/Loyola, sp/speaker-Duplikation der
TEI-Generierung (2330/3180/2540/2400; auf 2330 S.234 erfundene Sprecherstruktur),
OCR-Halluzinationen (900 S.2 Schleife, 1520 S.130 Phantomseite), Faksimile-Versatz
Dok 680, 2300 (Verlagsdeckblatt), 1220.

## Recall (40 Seiten, erschoepfend gelesen)

67 Nennungen gelisteter Entitaeten: 20 hit, 17 on_worklist, 30 missed (Abdeckung 0.552).
Ursachen: 28 rule_gap, 2 lexicon_gap, 0 OCR. Reparaturklassen nach Ertrag: Sprecherkuerzel
in Interviews (J.H., G.D.K., HERSCH-Labels), Byline-Ausnahme der Autorin (bewusste Regel,
4 Luecken; Hersch-Umfangsfrage jetzt mit Zahlen), Akronym-Kleinschreibung (l'Unesco),
GND-Klammerqualifikator nicht abgestreift (Bund, Le populaire), adjektivische Inversion
(Genfer Universitaet), Wortgrenze vor Fussnotenziffer (Nietzsche2).

## Naechste Schritte

Konventionsentscheid Seitenapparat, dann zweite Lesart der Praezision; Reparaturklassen
als Matcher-Wave; Generator-Defekte (sp/speaker, 3040-Bibliographie) in die Struktur-Spur;
Seitenzuordnungs-Reparatur 120/1350/680/2300 operator-gated; danach neu ziehen und
nachmessen.
