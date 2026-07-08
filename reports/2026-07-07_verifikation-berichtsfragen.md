# Verifikation der Berichtsfragen (A bis G)

Datierter Snapshot, 2026-07-07. Übergabe an die Instanz, die den finalen Bericht (`knowledge/final-report.md`) hält. Jeder Befund trägt seinen Beleg als Kommando, Dateipfad mit Zeilennummer oder gemessenen Wert mit benannter Quelle. Gemessenes ist von Inferenz getrennt; Inferenzen sind als solche markiert und tragen eine Konfidenz. Als datierter Report ist dieses Dokument von der Regel gegen volatile Mengen ausgenommen, die Zahlen sind hier der Gegenstand.

## Rahmen und ein Vorbehalt zum Arbeitsstand

Alle Läufe stammen aus dem Repository-Arbeitsstand vom 2026-07-07 gegen `output/tei_final` und die generierten Mirror-Daten. Das Repository wird zeitgleich von mehreren Claude-Instanzen bearbeitet. Die inhaltliche Prüf-Ebene (Abschnitt B) wird gerade von einer parallelen Instanz gebaut; die vier zugehörigen eval-Audit-Skripte und ihre Tests sind untracked und tragen den heutigen Zeitstempel. Ihre Ergebnisse sind reproduzierbar, ihr Commit ist operator-gated und mit der bauenden Instanz abzustimmen.

## A. Verifikation der bereits getroffenen Aussagen

### A1. Schemavalidität aller 285 finalen TEI

Gemessen. `python -m scripts.tei.tei_validator --all --report` läuft mit Exit-Status 0 über 285 Dokumente. Ergebnis: 285 valide gegen `data/schema/zbz_hersch.rng`, 0 invalid, 255 mit Warnings. Quelle ist der frisch erzeugte Bericht `output/tei_final/validation_report.json`. Blockierend verletzte Regeln (RelaxNG plus Error-Regeln) zählt der Lauf mit 0. Die 255 Dokumente mit Warnings tragen ausschließlich die informativen W-Regeln. Das Schema-Gate `python -m pytest tests/test_tei_schema.py -q` bestätigt das mit 289 passed, Exit-Status 0.

Für den Bericht bedeutet das eine Dreiteilung, die klar zu benennen ist. Schemavalide sind 285 von 285. Blockierende Projektregeln verletzt keines. Nur informative Hinweise tragen 255.

### A2. Texterkennung auf dem Niveau der ZBZ-Referenz

Die Aussage beruht auf dem Korpuslauf mit n = 25 Ground-Truth-Dokumenten, nicht auf zwei tiefengeprüften Dokumenten. Gemessen aus `docs/data/cer_statistics.json`, Block `overall.end_to_end_fidelity`:

- Mean 2,08 % (`0.020794`)
- Median 1,28 % (`0.012763`)
- Q1 1,03 %, Q3 2,56 %, Max 5,87 % (Doc 1440)

Aktualisierung 2026-07-08: die Werte sind auf den aktuellen Headline-Stand nach der Doc-30-Reparatur gebracht (E98/E99). Der frühere Maximalwert 11,59 % (Doc 30) ist mit der gezielten Neu-OCR der Doppelseite auf 0,90 % gefallen, der Korpus-Maximalwert liegt jetzt bei Doc 1440. Quelle unverändert `overall.end_to_end_fidelity` in `docs/data/cer_statistics.json`.

Der im Zwischenstand genannte Median von 1,83 % steht in keiner Repo-Datei. Er ist durch 1,28 % zu ersetzen.

Ein Vorbehalt ist mitzuführen, der ebenfalls aus der JSON stammt. Der Block `selection_bias` markiert die Variable `n_chars` mit `comparable=false` (KS-Test p = 0,0139); die vier weiteren Variablen (Sprache, Layout-Typ, Publikationsform, Seitenzahl) sind vergleichbar. Die JSON selbst formuliert die Konsequenz, das Selektions-Subset weiche auf `n_chars` signifikant vom Korpus ab, eine Generalisierung auf das Gesamtkorpus erfordere Vorsicht. Die Aussage trägt damit als Korpusmedian über 25 Ground-Truth-Dokumente. Eine Aussage über alle 285 folgt daraus nur mit dem deklarierten Vorbehalt.

### A3. „In beiden Dokumenten an denselben Stellen"

Die Prämisse ist auf der Platte nicht gedeckt. Der Report belegt in `knowledge/final-report.md` §6.2 mit fünf verschiedenen Dokumenten, je eines pro Beispiel:

| Beispiel | Doc-ID | Typ, Sprache, Form | Zeile |
|---|---|---|---|
| 1 | 130 | A, FR, journalArticle | 517 |
| 2 | 1060 | A, DE, other | 538 |
| 3 | 2530 | B, FR, journalArticle | 558 |
| 4 | 1330 | D, FR/DE, book | 578 |
| 5 | 1440 | B, DE, book | 601 |

Alle fünf stammen aus dem 25er-Ground-Truth-Set. Ein Prüfprotokoll „zwei tiefengeprüfte Dokumente an denselben Stellen" existiert als Datei nicht. Die realen Verifikationsartefakte sind `reports/2026-07-07_ground-truth-landkarte.md` (systematische Lesung aller 25 Referenzen gegen die Editionsrichtlinien) und `reports/cer-gegenprobe-2026-07-03.md` (Docs 30, 760, 1440). Konfidenz hoch. Die Zwei-Dokument-Formulierung ist im Zwischenstand durch die reale Fünf-Beispiel-Struktur zu ersetzen.

## B. Inhaltliche Fehlerklassen

### B4. Korpusweite Implementierung der fünf Klassen

Verifizierter Stand auf der Platte. Drei der genannten Prüfungen sind als eigene eval-Audits korpusweit implementiert, nicht über den Validator-W-Katalog. Alle drei Skripte plus ein viertes (`relation_integrity_audit.py`) sind untracked und tragen den heutigen Zeitstempel.

| Klasse | Korpusweit | Beleg | Trefferzahl aus dem Lauf |
|---|---|---|---|
| 1 Seitenzahl im Fließtext | ja | `scripts/eval/pb_number_audit.py`, Signal `digit_paragraphs` plus `layout_mismatch` | digit_paragraphs u.a. 2780:83, 660:67; Layout/pb-Mismatch 2330:189, 1520:100 |
| 2 Doppelseite als Einzelseite | nur als Symptom | Validator W19 plus `scripts/eval/reading_order_audit.py`; dedizierter Detektor mit E73 entfernt | W19 831 Seiten Umsortierung, 274 fragil; Textverlust 30/760 als Einzelfall (n ≈ 2) |
| 3 Titelblätter, Bibliotheksvermerke | nein | keine Prüfung | Stichprobe (`final-report.md` Z. 806) |
| 4 Kursivverlust | ja (neu) | `scripts/eval/hi_preservation_audit.py` | 18 Seiten in 12 Dokumenten mit Emphasis-Signal ohne `<hi>` |
| 5 Zeichennormalisierung | ja | `scripts/eval/char_lint_audit.py`, vier Regelklassen | u.a. Guillemet und Space-vor-Interpunktion 2330:1313, 1520:399 |

Kommandos für die Zahlen: `python -m scripts.eval.pb_number_audit`, `python -m scripts.eval.char_lint_audit`, `python -m scripts.eval.hi_preservation_audit`. Die korpusweiten Aggregate liegen in `output/audits/*.json`.

Zwei Klassen bleiben strukturell unsichtbar. Klasse 3 ist eine semantische Zugehörigkeit ohne formales TEI-Korrelat; ein RelaxNG-Schema und die strukturellen W-Regeln sehen Elementtypen und Attribute, nicht die editorische Zugehörigkeit eines Textinhalts. Klasse 4 wäre ohne den neuen Audit ebenfalls unsichtbar, weil fehlendes `<hi>` wohlgeformtes, schemavalides TEI mit korrektem Textinhalt ergibt. Der Audit umgeht das, indem er das Markdown-Emphasis-Signal der Basis-OCR gegen das gelieferte TEI hält.

### B5. Kursivverlust und CER

Bestätigt, doppelt belegt. Gelesen in `extract_text_for_comparison` (`scripts/eval/evaluate_ocr.py:258-289`): die rekursive `get_text` behandelt `<hi>` nicht gesondert und extrahiert den Innentext identisch, unabhängig vom Markup. Der Report bestätigt es am Beispiel 4, Doc 1330 (`final-report.md:588-599`). Dort wird `*Titel*` gegen `<hi rendition="#i">Titel</hi>` verglichen, E9 entfernt `<hi>` beidseitig, die Differenz ist 0. Verlorene Kursivauszeichnung erzeugt damit keinen CER-Beitrag. Das ist der methodische Grund, warum eine niedrige Fidelity-CER und ein seitenweiser Kursivverlust gleichzeitig zutreffen. Dieser Zusammenhang gehört in den Bericht.

### B6. Ursache und Vollständigkeit des Kursivverlusts

Der Verlust entsteht als Modellentscheidung in Step 2. Der Mapping-Prompt weist die Auszeichnung an (`scripts/tei/tei_mapping_prompt.py:94`, „Italic text | `<hi>` | rendition=\"#i\" | Verify from image"). Die nachgelagerte Bereinigung `fix_gemini_tei` behält `<hi>` (`scripts/tei/tei_step2.py:178`, `inline_tags` enthält `"hi"`). Eine nachgelagerte Entfernung findet nicht statt.

„Vollständig" ist widerlegt. Die Auszeichnung verwendet die ZBZ-Satzspiegel-Notation `rendition="#i"`, nicht `rend="italic"`. Sie steht in 129 der 285 finalen TEI (697 Vorkommen), gemessen per Grep über `output/tei_final`. Der Audit `hi_preservation_audit` findet nur 18 Seiten in 12 Dokumenten mit verlorener Emphasis; davon tragen 10 Dokumente an anderer Stelle `<hi>`, nur 2 (470, 660) tragen gar keines. Der Verlust ist seitenweise und lokal, er sitzt dort, wo das Modell die Kursivierung aus dem Overlay-Bild nicht rekonstruiert. Konfidenz hoch. Die Berichtsaussage „vollständiger Kursivverlust" ist auf „lokal, 18 Seiten" zu korrigieren.

## C. Seitenzahlen und Doppelseiten

### C7. Seitenzahl-Übernahme

Deterministisch, ohne Bildlesen. `detect_page_number` (`scripts/tei/tei_step1.py:61-72`) liest die gedruckte Zahl per Regex aus einer `_filter`/`_skip`-Chrome-Region des Layout-Stroms. `drop_filter_echoes` (Z. 75) verwirft den zugehörigen Echo-Absatz vor dem Matching. Der Prompt setzt `<pb n="{printed_num}">` (`tei_mapping_prompt.py:52`). Die Originalzahl ist damit aus dem OCR- und Chrome-Text verfügbar, sofern das Layout die Fußzeile als `_filter` klassifiziert hat. Landet die Zahl im Fließtext, hat das Layout-Matching die Chrome-Region nicht isoliert. Der Kommentar `tei_step1.py:26-33` benennt beide Defekte als eine Ursache. Der Vorschlag, die Zahl fest zu verdrahten, ist damit tragfähig. Konfidenz hoch.

### C8. Doppelseiten-Erkennung

Verfügbare Signale, teils verifiziert. Eine Seitenformat-Heuristik (`page_ratio >= 1.5 -> 'partial'`) existierte und wurde mit E73 entfernt; sie ist in `scripts/eval/cer_statistics_runner.py:66-69` als wirkungslos dokumentiert (Inferenz mittel, nicht im Detail nachgelesen). Der Layout-Prompt Typ D weist die Zwei-Hälften-Erkennung für Querformat explizit an (`scripts/layout/layout_qa_gemini.py:63`). Das geometrische Signal liegt im Layout-JSON als `image_width` und `image_height`, also als Seitenverhältnis. Nicht verifiziert ist, ob das Masterfile ein explizites Doppelseiten-Feld trägt; diese Datei wurde nicht geöffnet. Konfidenz hoch für das Aspect-Ratio-Signal, offen für das Masterfile.

## D. Layout-Evaluation

### D9. Transkribus-PAGE-XML als Layout-Ground-Truth

Verwertbar mit zwei Divergenzen. Gelesen in `data/source/transkribus_page_xml/100/page/0001_p002.xml`: absolute Pixel-Polygone (`imageWidth="2479"`, `imageHeight="3508"`, `Coords points`), eine `ReadingOrder` und Regionentypen über `custom="structure {type:page-number;}"`. Das Projekt-Layout (`docs/data/pages/40/40_p061_layout.json`) nutzt Prozent-Bboxes plus `label` und `zbz_tag`. Die Koordinatensysteme divergieren (Pixel gegen Prozent, umrechenbar über die mitgelieferten Bilddimensionen). Die Typsysteme divergieren (PAGE-Structure-Typen gegen Projekt-Labels). Eine IoU-Evaluation ist nach Pixel-zu-Prozent-Normalisierung möglich, die Typprüfung nur nach einer Mapping-Tabelle. Ein rein geometrischer IoU-Vergleich ohne Typprüfung ist direkt machbar. Konfidenz hoch.

### D10. Warnliste riskanter Seiten

Die Liste ist keine Datei, sondern regenerierbarer stdout. `python -m scripts.eval.reading_order_audit --worklist` gibt die fragilen Seiten je Dokument aus. Gemessen: 831 Seiten mit Umsortierung, davon 557 robust und 274 fragil, verteilt auf 145 Dokumente. Nach der Reassemble-Vorschau sinkt die W19-Menge auf 39 Restseiten (`reports/m3-reassemble-preview.md:13-14`). Die tatsächliche Fehlerquote der Liste gegen das Faksimile ist nicht beziffert; sie bräuchte visuelle Ground Truth. Das ist als Grenze zu deklarieren. Der Gegenbefund auf der dreispaltigen Doppelseite bleibt eine Einzelbeobachtung, solange die Trefferquote der ganzen Liste unbekannt ist. Konfidenz hoch.

### D11. Flächenabdeckungswert

`compute_page_quality` (`scripts/layout/layout_qa_gemini.py:324-349`) berechnet `coverage = sum(w_pct * h_pct / 100)` pro Seite und loggt ihn im Auto-Modus nach stdout (Z. 707-710); Werte unter 30 % lösen die Neuerkennung aus. Persistiert wird nicht die Coverage, sondern der Gemini-`score` (avg_score in der Summary). Die Korpus-Aggregation über 3985 Docling-Basisseiten ergibt Median 48,6 %, Mean 45,0 %. Unter der Neuerkennungs-Schwelle von 30 % liegen 900 Seiten, unter 15 % liegen 421 Seiten. Konfidenz hoch.

## E. Referenzqualität

### E12. Fehlerrate der Referenz

Trennbar, teils schon geleistet. Die Ground-Truth-Landkarte katalogisiert in §4 die bekannten Referenzfehler systematisch (19 Punkte, u.a. GND-Präfix-Drift, `corresp` gegen `ref`, der Transkriptionsfehler in Doc 1440, die nicht wohlgeformte Referenz 1520). Report-Beispiel 5 (Doc 1440) zählt einen Referenzfehler explizit gegen die Pipeline. Ein Faksimile-Abgleich über rund zweihundert Seiten könnte Referenzfehler von Pipeline-Fehlern getrennt quantifizieren; aktuell ist die Trennung qualitativ belegt und nicht beziffert. Die CER ist nach oben durch die Referenzqualität begrenzt. Diese Grenze ist zu deklarieren, sie ist keine bezifferte Größe. Konfidenz hoch.

## F. teiCrafter-Schnittstelle

teiCrafter liegt lokal unter `ResearchTools/teiCrafter` (über `Vault Operations/Repo-Verzeichnis.md` lokalisiert und gelesen).

### F13. Übergebenes TEI und Kurationsschritt

Es geht das finale `output/tei_final/{doc}_final.xml` über, teiCrafters natives Format, das direkt ohne Konversion öffnet (`knowledge/ecosystem-synthesis.md:68-70`; `teiCrafter/knowledge/integration.md:246-250`). Die Viewer-Kuration ist optional und keine Vorbedingung; teiCrafter ist selbst der Kurationsschritt. Konfidenz hoch.

### F14. Erwartetes TEI-Subset

Zwei Richtungen. Eingangsseitig erwartet teiCrafter kein Subset; ein generischer, verlustfreier Reader liest beliebiges TEI per local-name (`teiCrafter/knowledge/integration.md:76-78`). `{doc}_final.xml` deckt sich damit. Ausgangsseitig divergiert das teiCrafter-Modell. Sein Entity-Register (`standOff` mit GeoNames und Wikidata) verletzt das mit E88 auf Inline-GND für Person, Organisation und Werk verengte `zbz_hersch.rng` (`knowledge/decisions.md:239-241`; `data/schema/zbz_hersch.rng:3757`). Eine Transformation an der teiCrafter-Ausgabe ist nötig und laut E88 noch offen. Konfidenz hoch.

### F15. NER, NEL und Implementierungsstand der Übergabe

Die NER- und NEL-Anreicherung ist aus der Pipeline entfernt (E71) und in teiCrafter angesiedelt, ein getrennter, stromabwärtiger Expert-in-the-Loop-Schritt (`knowledge/project.md:141,163`; `teiCrafter/knowledge/integration.md:104-108`). Die Übergabe existiert als manuelles File-Open und funktioniert heute für Text; eine automatisierte Export- oder Import-Bridge gibt es nicht (`integration.md:246-250`). Die schema-konforme Inline-GND-Rückführung ist noch nicht implementiert. Konfidenz hoch für Verortung und Bridge-Stand, mittel für den internen ID-Vergabemechanismus in teiCrafter.

## G. Datenbeispiele für Kapitel 4

### G16. OCR-Beispiel (4.2)

Doc 810, `output/mistral_results/810_p3.md` (verifiziert vorhanden). Mistral emittiert seitenweises Markdown mit Tabellen, hier die Teilnehmerliste der Bergedorfer Gespräche als Markdown-Tabelle. Die automatische Aufteilung großer Dokumente steht in `scripts/ocr/ocr_pipeline.py:65-89`, `_split_pdf(max_pages=30)`, aufgerufen in Zeile 131; der Schwellwert `MISTRAL_MAX_PAGES_PER_REQUEST = 30` liegt in `scripts/config.py:80`, der Seitenoffset wird über `page_offset` fortgeschrieben (Z. 159-160). Konfidenz hoch.

### G17. Layout-Beispiel (4.3)

Doc 1520, Seite 12, beide Dateien vorhanden. `docs/data/pages/1520/1520_p012_layout.json` (Docling, 21 Regionen, Bibliografie-Einträge als `list_item`/`zb_paragraph`) gegen `docs/data/pages/1520/1520_p012_layout_gemini.json` (16 Regionen, umgelabelt zu `zb_heading`, Blöcke gemergt, Reihenfolge korrigiert). Protokollfelder der Gemini-QA in der `_gemini.json`: `score=80`, `num_corrections=12`, `issues` nennt die Fehllabelung der Bibliografie-Einträge. Der Flächenabdeckungswert ist berechnet und nicht in der JSON persistiert; die Korpus-Verteilung steht in D11. Die dreispaltige Doppelseite als Kandidat für die korrekte Lesereihenfolge liefern die Layout-Typen C und D (Docs 40, 1520, 760, 830, 300). Konfidenz hoch.

### G18. TEI-Erzeugungs-Beispiel (4.4)

Die Zwischenartefakte liegen real vor. `output/tei_unified/1520/1520_p012_scaffold.xml` (Step 1, deterministisch, `<div>`, `<pb>`, `<head>`, `<p>`, `<lb>` mit `facs`-Zeigern, ohne Auszeichnung) gegen `output/tei_unified/1520/1520_p012_refined.xml` (Step 2, `<div type="bibliography">`, `<listBibl>`, `<bibl>`, plus `<persName ref="GND:...">`, `<orgName>`, `<foreign xml:lang>`). Für den Kursivverlust am Modellurteil ist Doc 1330 (Report-Beispiel 4, `final-report.md:592-599`) das schärfere Beispiel, weil die Referenz dort belegbar `<hi rendition="#i">` trägt und Step 2 die Auszeichnung aus dem Bild nachbilden soll. Ein sekundärer Beleg für den seitenweisen Verlust liegt in `1520_p012_refined.xml`, das kein `<hi>` enthält, während `1520_final.xml` insgesamt 54 trägt. Konfidenz hoch für Mechanik und Notation, mittel für die Kursiv-Erwartung auf p012 ohne Faksimile-Sicht.

### G19. Round-Trip-Beispiel (6.1)

Ein realer, im Viewer durchgeführter Round-Trip existiert für Doc 30. Auf der Platte liegen `output/ocr_curated/30_p1.md` bis `30_p4.md` und `output/layout/30/30_p001_layout_curated.json` bis `p004` (verifiziert vorhanden). Was `--reassemble` konsumiert, gelesen in `scripts/tei/tei_unified.py`: Step 1 wird erzwungen neu gerechnet (`force_step1 = force or reassemble`, Z. 173), Step 2 kommt aus dem `_refined.xml`-Cache (Z. 203-208), der Stale-Check `_refined_is_stale` (Z. 55-80) prüft `OCR_CURATED_DIR` und das `_curated`-Layout und refined selektiv nur die geänderte Seite. Der Aufruf lautet `python -m scripts.tei.tei_unified --doc 30 --reassemble`. Eine Einschränkung steht in `knowledge/workflow.md:365`: Gemini leitet den Text beim Refinement neu ab, eine OCR-Kuration ist Vorschlag; für wortgenaue Änderungen schreibt der TEI-XML-Modus direkt `output/tei_final/{doc}_final.xml` an der Pipeline vorbei. Ein tatsächlicher Reassemble-Durchlauf wurde nicht ausgeführt, weil er Auslieferungsdaten verändert und operator-gated ist. Konfidenz hoch.

## Korrekturen am Zwischenstand und am Bericht

Drei Aussagen sind gegen die Platte zu korrigieren.

1. Der Fidelity-CER-Median beträgt 1,28 %, der Mean 2,08 % (Stand nach E98/E99), nicht 1,83 %. Die Aussage trägt als Korpusmedian über 25 Ground-Truth-Dokumente mit dem Selektionsbias-Vorbehalt auf `n_chars`.
2. Der Report belegt mit fünf verschiedenen Dokumenten (130, 1060, 2530, 1330, 1440), je eines pro Beispiel. Eine Formulierung „zwei tiefengeprüfte Dokumente an denselben Stellen" ist auf der Platte nicht gedeckt.
3. Der Kursivverlust ist lokal und umfasst 18 Seiten in 12 Dokumenten. „Vollständig" trifft nicht zu; die Kursiv-Notation `rendition="#i"` steht in 129 der 285 finalen TEI.

Ein vierter Punkt betrifft den Arbeitsstand. Die inhaltliche Prüf-Ebene aus Abschnitt B (vier eval-Audits plus Tests) ist untracked und heute von einer parallelen Instanz entstanden. Vor einer Berichtsaussage über diese Audits ist ihr Stand mit der bauenden Instanz abzustimmen.
