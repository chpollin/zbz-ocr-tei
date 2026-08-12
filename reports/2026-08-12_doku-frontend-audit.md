# Frischeaudit, statische Seiten und Konstitution, 2026-08-12

Geprueft wurden `docs/index.html`, `docs/methode.html`, `docs/about.html`, `docs/impressum.html`,
`README.md` und `CLAUDE.md` gegen den tatsaechlichen Repo-Zustand. Ausgenommen sind `docs/viewer.html`
und `docs/folien-entitaetsannotation.html`, beide in paralleler Ueberarbeitung. Pruefquellen sind
`docs/data/cer_statistics.json` fuer alle CER-Werte, `knowledge/project.md` und `knowledge/pipeline.md`
fuer Korpus und Pipeline, `knowledge/entity-integration.md`, `knowledge/entity-evaluation.md` und
`knowledge/decisions.md` E99/E105/E106 fuer die Entity-Spur, dazu die generierten Artefakte
`docs/data/catalog.json`, `output/tei_final/{id}_manifest.json` und das Dateisystem selbst.

Alle Zeilenangaben wurden nach der Analyse erneut gegen die Datei geprueft. `CLAUDE.md` wird
waehrend dieser Sitzung von einer anderen Instanz bearbeitet, die Zeilennummern koennen sich
verschieben; der jeweils zitierte Wortlaut macht die Stelle unabhaengig davon auffindbar.

## 1. README erklaert Entity-Linking als aus dem Scope entfernt (FALSCH)

`README.md:78-80` sagt: "Removed from scope: NER / entity linking (GND/Wikidata). Implemented
earlier, removed (E71): in the delivered TEI only a small fraction of tagged mentions carried a real
GND id".

Die Entity-Spur ist wieder aufgebaut und gemessen. `knowledge/entity-integration.md:396-403` haelt
fest, dass M0 bis M3 erreicht sind, `reports/2026-08-12_entity-eval-ergebnis.md` weist Tier-1-Praezision
0.952 (Bootstrap-Intervall 0.925 bis 0.976) und Recall-Abdeckung 0.552 aus, E105 und E106 vom
2026-08-12 sind registriert. Auf der Platte liegen 287 Preview-Dateien unter `output/entity_preview/`,
4401 git-verfolgte Entity-Dateien unter `docs/data/`, und `docs/data/catalog.json` fuehrt fuer alle
285 Dokumente einen vierten Stream `entities`. Zutreffend bleibt allein, dass `tei_final` noch keine
Entity-Auszeichnung traegt, weil M5 bis M7 offen sind.

Fix: Den Absatz durch eine Zustandsbeschreibung ersetzen, die die Preview-Lage nennt (gemessen,
`tei_final` unangetastet, Bestandslauf operator-gated) und auf `knowledge/entity-integration.md`
sowie `knowledge/entity-evaluation.md` verweist. Achtung, `knowledge/pipeline.md:253-257` traegt
dieselbe veraltete Aussage ("Named entity markup was removed with E71"); ohne Korrektur dort
widerspricht das README seiner eigenen Quelle.

## 2. README stellt den Reading-Order-Rollout als genehmigungsreif dar (FALSCH)

`README.md:89-93` sagt: "The generator fix is built, and a reversible corpus-wide preview confirms
it corrects the large majority of affected pages (`reports/m3-reassemble-preview.md`) ... Rolling the
fix out rewrites the delivered TEI and awaits operator approval (M3 ... E90)". `README.md:96-97`
wiederholt das als offenen Punkt.

E99 (`knowledge/decisions.md:398-404`, 2026-07-07) hat genau das widerlegt. Die Anwendung auf Kopien
aller 25 Referenzdokumente ergab 0 Verbesserungen und 9 Verschlechterungen bis +40 Prozentpunkte.
Die Entscheidung lautet, kein maschinelles Reordering des ausgelieferten Korpus auf beiden Wegen,
W19 wird als Text-oder-Zonen-Verdachtssignal umgedeutet, und die Preview vom 2026-06-21 ist obsolet
und darf nicht promoviert werden. `output/tei_preview/` liegt weiterhin auf der Platte.

Fix: Die bekannte Einschraenkung auf den E99-Stand umschreiben (korrupte Zonen-Zuordnung ueber
korrektem Text, Aufloesung durch Faksimile-Kuration) und den Pending-Punkt streichen. Auch hier
traegt `knowledge/project.md:150-154` und `:237` noch den alten M3-Stand, die Korrektur muss dort
mitlaufen. Dieser Befund hat operatives Risiko, weil das README zu einem Lauf einlaedt, den die
Messung als schaedlich ausgewiesen hat.

## 3. about.html veroeffentlicht eine ueberholte CER-Headline (VERALTET)

`docs/about.html:84-85` sagt: "Fidelity CER (real OCR and transcription errors): mean 2.71 %,
median 1.40 % (n = 25, BCa bootstrap, B = 10,000, seed 42)".

`docs/data/cer_statistics.json` weist `overall.end_to_end_fidelity.mean` 0.020794 und `median`
0.012763 aus, also 2.08 Prozent und 1.28 Prozent. Die Werte 2.71 und 1.40 stammen aus dem Stand vom
2026-06-10 und wurden durch E98 und E101 abgeloest. `docs/methode.html:75` fuehrt die aktuellen
Werte bereits, die Website widerspricht sich also intern auf zwei Seiten.

Fix: Beide Zahlen ersetzen, oder besser den Satz auf die Methodenseite verweisen lassen, damit die
Zahl nur an einer Stelle steht.

## 4. README nennt eine Datei, die es nicht gibt (FALSCH)

`README.md:134` sagt: "cp .env.example .env".

Im Repo-Wurzelverzeichnis existieren als Dotfiles `.claude`, `.claudeignore`, `.env`, `.git`,
`.github`, `.gitignore`, `.pytest_cache`, `.venv` und `.vscode`. Eine Vorlagendatei
`.env.example` gibt es nicht, ebenso wenig `.env.sample` oder `env.example`. Der Getting-Started-Pfad
bricht damit an seiner zweiten Zeile ab.

Fix: Entweder die benoetigten Variablennamen direkt im README nennen (ohne Werte) oder die
Vorlagendatei anlegen.

## 5. Konstitution nennt einen Namensraum, den es nicht gibt (VERALTET)

`CLAUDE.md:52` sagt: "Frontend: ES6+ JavaScript ... `ZBZ.*` / `TeiViewer.*` namespaces".

Eine repoweite Suche ueber `.js`, `.html`, `.md` und `.py` findet `TeiViewer` ausschliesslich in
dieser Zeile selbst. Real existieren `window.ZBZ` (`docs/assets/js/core.js:309`) und der im
Dateikopf von `docs/assets/js/viewer.js` deklarierte Namensraum `ZBZ.Viewer`.

Fix: `ZBZ.*` / `ZBZ.Viewer` schreiben. Wirkung, weil die Konstitution neu erzeugten Frontend-Code
auf einen toten Namensraum lenkt.

## 6. Manifest-Datenmodell in der Konstitution kennt den vierten Stream nicht (LUECKE)

`CLAUDE.md:259-260` beschreibt das Manifest mit "`streams.{ocr,layout,tei}.status`" und
"`streams.{ocr,layout,tei}.history`".

`output/tei_final/30_manifest.json` und der Spiegel `docs/data/manifests/30_manifest.json` tragen
vier Streams, den zusaetzlichen `entities` mit `source: entity_preview`. `docs/data/catalog.json`
fuehrt den Stream fuer alle 285 Dokumente, `docs/index.html:64` bietet ihn als Filterwert an.

Fix: `entities` in beide Aufzaehlungen aufnehmen und in einem Halbsatz kennzeichnen, dass er die
Preview-Schicht abbildet und nicht den ausgelieferten TEI-Stand.

## 7. Versionierungsregel nennt nur eine Ausnahme, real gibt es zwei (LUECKE)

`CLAUDE.md:9` sagt: "Do not version output: generated files belong in `output/` (gitignored). The
exception is `data/curated_tei/` (reserved for hand-verified TEI, currently empty)".

`git ls-files docs/data` liefert 21578 verfolgte Dateien. `docs/data/` ist ein bewusst
mitversionierter generierter Spiegel, was `CLAUDE.md:93` selbst als "GENERATED mirror" und
`CLAUDE.md:155` als "versioned as evidence" beschreibt. Die Regel an der prominentesten Stelle
widerspricht den beiden spaeteren Stellen.

Fix: Die zweite Ausnahme benennen und begruenden (der Spiegel traegt die GitHub-Pages-Auslieferung),
damit die Regel nicht als Verbot gelesen wird.

## 8. Reassembly-Preview steht ohne den E99-Vorbehalt in der Diagnoseliste (VERALTET)

`CLAUDE.md:140` sagt: "`python -m scripts.tei.tei_reassemble_preview --all` # M3 dry run: reassembly
preview -> output/tei_preview + report, tei_final untouched".

Die unmittelbar benachbarte Zeile 132 traegt fuer das Schwesterwerkzeug den Vorbehalt "corpus
reorder empirically refuted (E99)". Fuer die Preview fehlt er, obwohl E99 sie ausdruecklich als
obsolet erklaert und ihre Promotion untersagt.

Fix: Denselben Vorbehalt anhaengen oder die Zeile streichen, da das Artefakt nur noch Beweismittel
ist.

## 9. about.html kennt die Entity-Schicht nicht (LUECKE)

`docs/about.html:49-54` zaehlt unter "What this tool does" Inspektion, manuelle Korrektur,
Workflow-Status und Demonstration auf; `docs/about.html:71-77` fuehrt die Pipeline in fuenf
Schritten ohne Entity-Schritt; `docs/about.html:100-103` beschreibt die Architektur ohne
Entity-Spiegel.

Die Katalogseite zeigt die Schicht bereits, `docs/index.html:64` als Filter und die Ampel je
Dokument, und der Viewer hat einen Entity-Modus. Das Schweigen der About-Seite ist damit eine
Luecke und keine vertretbare Scope-Grenze, weil dieselbe Site die Schicht an anderer Stelle sichtbar
macht.

Fix: Ein Aufzaehlungspunkt und ein Pipeline-Eintrag, beide mit dem Zusatz, dass die Schicht als
read-only Preview vorliegt und der ausgelieferte TEI-Bestand sie nicht traegt.

## 10. README-Dokumentationstabelle fuehrt sechs Wissensdokumente nicht (LUECKE)

`README.md:148-160` listet zehn Eintraege.

Unter `knowledge/` liegen sechzehn Dokumente. Es fehlen `cer-methodology.md`,
`literature-comparison.md`, `ground-truth-map.md`, `entity-integration.md`, `entity-evaluation.md`
und `agent-orchestration.md`. `CLAUDE.md:19-35` fuehrt sie vollstaendig, das README hinkt also der
Konstitution nach. Zusaetzlich beschreibt `README.md:113-115` den Viewer ohne den Entity-Stream.

Fix: Sechs Zeilen ergaenzen und im Frontend-Absatz einen Halbsatz zum Entity-Stream setzen.

## 11. Demo-Faksimiles, vier genannt, fuenf ausgeliefert (VERALTET)

`README.md:102-103` sagt: "Live facsimile images: only four demo documents are committed (`1000`,
`1330`, `1540`, `2310`); the rest are local-only, so the GitHub Pages viewer shows scans only for
those four".

`git ls-files docs/images` liefert fuenf Dokumentordner, zusaetzlich `1620` mit fuenf Seiten aus
Commit e4f641cd von heute. Da weder `catalog.js` noch `viewer.js` das `demo`-Flag auswerten, zeigt
die Pages-Instanz die Scans fuer alle fuenf.

Nebenbefund, `FEATURED_DOCS` in `scripts/edition/generate_edition_data.py:41` fuehrt weiterhin vier
Ids, weshalb `1620` in `catalog.json` als `demo: false` und nicht in `featured` steht. Die neu
committeten Bilder erscheinen daher weder in der Featured-Auswahl noch in der Verifikationszaehlung
des Generators.

Fix: Die Aufzaehlung im README um `1620` erweitern und `FEATURED_DOCS` nachziehen, falls das
Dokument als Demo gemeint war.

## 12. Regenerierungsdatum der Statistik um einen Tag verschoben (FALSCH)

`docs/methode.html:41-42` sagt: "Scientifically grounded CER evaluation, last regenerated
2026-07-08".

`docs/data/cer_statistics.json` traegt `meta.generated_at` 2026-07-09T10:01:06. Die letzte
Regenerierung erfolgte im Zuge von E103, die laut Register nur Literatur- und Meta-Felder veraendert
hat; die Messwerte blieben byte-identisch.

Fix: Datum auf 2026-07-09 setzen.

## 13. Workflow-Status wird als korpusweit einheitlich beschrieben (VERALTET)

`README.md:19` sagt: "The per-stream workflow status (OCR / Layout / TEI, E66/E67) is `unverified`
across the corpus". `docs/about.html:65` formuliert es als "currently reads 'unverified' throughout".

`docs/data/catalog.json` weist fuer Dokument 30 `ocr` als `in_arbeit` und `layout` als `verifiziert`
aus, mit Historie vom 2026-06-07. Beide Aussagen sind streng gelesen falsch, inhaltlich bleibt die
Aussage tragfaehig, dass `unverifiziert` der Uebergabe-Default ist.

Fix: "als Uebergabe-Default, mit vereinzelten Ausnahmen" formulieren oder auf den Katalog als
laufende Quelle verweisen. Ausserdem fehlt in beiden Aufzaehlungen der vierte Stream.

## 14. Entity-Gate-Zeile deckt sechs vorhandene Testmodule nicht ab (LUECKE)

`CLAUDE.md:226` fuehrt elf Testdateien als "entity gates".

Unter `tests/` liegen zusaetzlich `test_entity_corpus_digest.py`, `test_entity_eval_sample.py`,
`test_entity_gold_benchmark.py`, `test_entity_stream.py`, `test_entity_unlisted_scan.py` und
`test_variant_review.py`. Letzteres wird in `knowledge/entity-integration.md:210` ausdruecklich als
Gate des Variant-Review benannt. Wer das dokumentierte Gate laeuft, prueft sechs Suiten nicht.

Fix: Die sechs Dateien in die Zeile aufnehmen.

## 15. Meilensteinbereich der Entity-Spur zu eng benannt (VERALTET)

`CLAUDE.md:211` ueberschreibt den Block mit "Entity integration (pilot M0-M3, plan:
knowledge/entity-integration.md)".

`knowledge/entity-integration.md:386-394` fuehrt M0 bis M7. M0 bis M3 sind erreicht, M4 hat
Instrument und Bericht, und der Block selbst listet mit `entity_gold_benchmark` bereits ein
M4-Werkzeug.

Fix: "M0-M7, erreicht bis M3" oder schlicht "Entity integration" ohne Bereichsangabe.

## 16. Verzeichnisbeschreibung kennt `data/entities/` nicht (LUECKE)

`CLAUDE.md:72` beschreibt `data/` mit `source/`, `schema/`, `curated_tei/` und der generierten
`doc_metadata.json`.

Real liegt daneben `data/entities/` mit fuenf git-verfolgten Dateien, `all_entities.json`,
`gnd_cache.json`, `legacy_mentions.json`, `variant_review.json` und `mention_verdicts.json`. Die
letztgenannte ist laut E106 der schnappschussgebundene Urteilsspeicher und damit
Projektautoritaet. Auch `data/README.md` fehlt in der Aufzaehlung.

Fix: `entities/` als git-verfolgte Autoritaetsdaten aufnehmen.

## 17. Datenbeschreibung der About-Seite unvollstaendig (KOSMETIK)

`docs/about.html:101-103` sagt: "Data: catalog.json plus a per-page mirror under `data/pages/` (all
285 docs) and thumbnails under `data/thumbs/`".

`docs/data/` enthaelt zusaetzlich `manifests/`, `entities.json` und `cer_statistics.json`.

Fix: Die drei Eintraege ergaenzen, sofern die Aufzaehlung vollstaendig sein soll.

## 18. HCPR-Intervall nach oben gerundet (KOSMETIK)

`docs/methode.html:79` gibt das Intervall als "[99.6, 100]" an.

`domain_metrics.hcpr.overall.score_ci95` lautet [0.995992, 0.999618], also [99.6, 99.96]. Die obere
Grenze wird auf einen Wert gerundet, den die Messung nicht erreicht.

Fix: 99.96 schreiben oder auf eine Nachkommastelle konsistent runden.

## 19. Entity-Preview nur ueber den URL-Parameter dokumentiert (KOSMETIK)

`CLAUDE.md:229` sagt: "The viewer shows the previews read-only via
`viewer.html?doc={DOC_ID}&entities=1`".

Der Viewer traegt zusaetzlich einen Umschalter, `btn-entities` in `docs/assets/js/viewer.js`, der den
Parameter selbst setzt und entfernt.

Fix: Den Umschalter in einem Halbsatz nennen.

## 20. Methodenseite deckt nur die Textschicht ab (LUECKE, geringe Dringlichkeit)

`docs/methode.html` traegt den Titel "Method & Quality" und behandelt ausschliesslich die CER-Messung
der Textschicht.

Die Entity-Schicht hat mit dem Lauf vom 2026-08-12 eigene Guetezahlen, Praezision 0.952 mit
Bootstrap-Intervall, Inter-Annotator-Agreement 0.96 und Recall-Abdeckung 0.552, dokumentiert in
`knowledge/entity-evaluation.md` und `reports/2026-08-12_entity-eval-ergebnis.md`. Solange die
Schicht Preview bleibt, ist das Schweigen vertretbar; mit dem Bestandslauf M7 wird es zur Luecke,
weil die Seite sich als Qualitaetsautoritaet der Auslieferung praesentiert.

Fix: Ein kurzer Absatz mit Verweis, sobald die Schicht den ausgelieferten Bestand beruehrt.

## Als aktuell verifiziert, kein Handlungsbedarf

Interne Verweise. Alle 33 `href`- und `src`-Ziele der vier geprueften Seiten aufloesen auf
existierende Dateien, ebenso alle 54 relativen Markdown-Links in `README.md` und `CLAUDE.md`. Keine
toten Links. Externe Links wurden nicht abgerufen.

Kommandoreferenz. Jeder in `CLAUDE.md` genannte Modulpfad, jeder Skriptpfad und jede Testdatei
existiert, programmatisch geprueft, null Fehltreffer. Das schliesst die heute ergaenzten Eintraege
`blank_text_audit`, `build_mention_verdicts` und `entity_risk_ranking` ein.

Methodenseite gegen die Statistikquelle. Headline 2.08 und 1.28 mit Intervall [1.51, 2.73],
Volltext 18.36 und 9.59, Scope 16.28 und 7.03, Pipeline-Gewinn -10.08 Prozentpunkte bei p = 0.0034
und 17 von 25 verbesserten Dokumenten, HCPR-Punktwert 99.8, Schichtungstabellen nach Layouttyp und
Sprache, Stabilitaetspilot 0.04 sowie 0.13 und 0.25 Prozentpunkte, Korpusschaetzung 22.4 Prozent,
Selektionsbias p = 0.0139 auf `n_chars`. Alle Werte stimmen mit `docs/data/cer_statistics.json`
ueberein. Die Literaturzuschreibung folgt E103, Greif et al. arXiv:2504.00414 fuer die vier
Print-OCR-Werte, Levchenko mit der begutachteten RANLP-Fassung.

Katalogseite. `docs/index.html` traegt den Entity-Stream als Filter, die dreistufige Statuslegende
nach E77 und die vier Layouttypen, alles deckungsgleich mit `catalog.json` und `catalog.js`.

Frontend-Abhaengigkeiten der Konstitution. OpenSeadragon 5.0.1 ueber jsDelivr ist in `viewer.html`
so eingebunden; die Aussage zu JSZip ("not yet included in the code") stimmt, im gesamten
`docs/`-Baum findet sich kein JSZip-Verweis.

Struktur- und Korpusaussagen. `data/curated_tei/` ist leer bis auf `.gitkeep`; die Domaenengruppierung
unter `scripts/` und die Unterverzeichnisse von `docs/` entsprechen der Beschreibung; die
Engine-Angaben der About-Seite (Mistral Document AI 2512 auf Azure, Docling 2.75, Gemini 3.1 Flash
Lite) decken sich mit `knowledge/pipeline.md`; die Korpuszahlen der About-Seite (286 geliefert, 285
mit finalem TEI, rund 4100 Seiten, Sprachanteile) decken sich mit dem Korpustrichter in
`knowledge/project.md`.

Weitere gepruefte Einzelaussagen. Die Schemaaussage der Methodenseite (`zbz_hersch.rng` als alleinige
Formatautoritaet) folgt E102; die Journalaussage in `CLAUDE.md:7` (Sitzungen 1 bis 68 im kompakten
Archiv) deckt sich mit `knowledge/journal.md:60` und `:1016`; die Kennzeichnung der Entity-Spur als
dreistufiges Matching in `CLAUDE.md:30` deckt sich mit `knowledge/entity-integration.md:130`.
`docs/impressum.html` enthaelt keine ueberpruefbare Zustandsaussage und bleibt unveraendert gueltig.

Strukturaenderungen ohne Widerspruch auf den geprueften Seiten. Die TEI-XML-Seitenscheibe (49c5ee7a)
und die einzeilige Dokumentleiste (e7f9dd6d) betreffen nur den Viewer; weder README noch About-Seite
behaupten etwas, das ihnen widerspricht. Die Journalverdichtung (7cf84b23) laesst die
Archivaussage der Konstitution unberuehrt.
