# Promptotyping Commands, Artifacts und Tools

## Operative Schichten der Promptotyping-Methodik in der Implementation-Phase

---

### Begriffsklärung

**Promptotyping** ist eine vierphasige Context-Engineering-Methode (Preparation, Exploration, Distillation, Implementation). Das vorliegende Dokument behandelt die Implementation-Phase, in der ein konkretes Projekt mit einem konkreten Repository vorliegt und Agents darin arbeiten. Das laufende Editionsprojekt für die Zentralbibliothek Zürich (Nachlass Jeanne Hersch, 286 Dokumente) dient als durchgängiges Beispiel, an dem die beschriebenen Konzepte konkretisiert werden.

**Promptotyping Commands** bezeichnen die konzeptionelle Logik, nach der Agents in einem Projekt operieren. Commands definieren, welche Operationen in welcher Reihenfolge ausgeführt werden, unter welchen Bedingungen eine Operation wiederholt oder übersprungen wird und an welchen Punkten menschliche Entscheidungen erforderlich sind. Commands sind nicht ausführbar. Sie beschreiben Entscheidungsregeln. Im ZBZ-Projekt regelt ein Command beispielsweise, dass Claude Code nach jeder TEI-Korrektur eine RelaxNG-Validierung ausführt, bevor das nächste Dokument bearbeitet wird.

**Promptotyping Artifacts** bezeichnen alle materiellen Ergebnisse, die der Promptotyping-Prozess erzeugt und die zugleich als Werkzeuge und Kontextinformationen für Agents verfügbar sind. Artifacts umfassen ausführbare Programme (Python-Scripts, CLI-Tools), maschinenlesbare Wissensartefakte (Entity-Indizes, Validierungsreports, Metadaten-Dateien), Kontextdokumente für Agents (`CLAUDE.md`, `CLAUDE-COMMANDS.md`, Knowledge-Dokumente) und Anwendungen für menschliche Nutzerinnen und Nutzer (Digitale Edition, Curation Editor, Dashboard). Im ZBZ-Projekt ist der Entity Index als TEI-XML mit Wikidata- und GND-Verlinkung ein zentrales Artifact: Er ist Output der Named Entity Recognition, Kontextwissen für die weitere Dokumentverarbeitung und Datengrundlage für die Entitäten-Navigation der Digitalen Edition gleichzeitig.

Der Unterschied zwischen Commands und Artifacts ist der zwischen Partitur und Instrumenten. Die Commands geben an, was wann gespielt wird. Die Artifacts sind das, womit gespielt wird und was dabei entsteht. `CLAUDE-COMMANDS.md` veranschaulicht die Schichtung: Als Datei im Repository ist es ein Artifact (maschinenlesbar, versioniert, wartbar). Inhaltlich beschreibt es Commands (die Entscheidungsregeln für den Agent). Die Materialisierung einer Regel als Artifact ist selbst ein Designakt innerhalb der Methodik.

**Promptotyping Tools** bezeichnen den Aufruf eines Artifacts durch einen Agent in einem konkreten Arbeitsschritt. Ein Python-Script wie `tei_validator.py` existiert als Artifact im Repository (versioniert, wartbar, dokumentiert). Es wird zum Tool in dem Moment, in dem Claude Code es in der Shell ausführt: `python -m scripts.tei.tei_validator --doc 290`. Der Command bestimmt, *wann* dieses Tool aufgerufen wird: "Nach jeder TEI-Korrektur validieren."

Die Dreischichtung — Command (Entscheidungsregel), Artifact (materielles Werkzeug), Tool (konkreter Aufruf) — bildet die operative Grammatik der Promptotyping-Methodik. Commands ohne Artifacts bleiben abstrakt. Artifacts ohne Commands liegen ungenutzt im Repository. Tools ohne Commands sind Ad-hoc-Aktionen ohne Systematik. Erst das Zusammenspiel aller drei Schichten erzeugt den zyklischen, qualitätsgesicherten Arbeitsprozess, den Promptotyping beschreibt. Im ZBZ-Projekt dokumentiert `CLAUDE-COMMANDS.md` explizit alle drei Schichten: Die Befehle (welche Scripts existieren, welche Flags sie haben), die Zyklusregeln (in welcher Reihenfolge, unter welchen Bedingungen) und die Konventionen (Pfade, Sicherheitsregeln, Additivitätsprinzip).

---

### Die Ausgangslage: Zuverlässigkeit ist eine Infrastruktureigenschaft

Die erste Generation autonomer Agent-Frameworks (AutoGPT, BabyAGI, 2023) scheiterte an der Unzuverlässigkeit der zugrunde liegenden Modelle. Zwischen 2023 und Anfang 2026 hat sich die Situation grundlegend verändert. Auf dem SWE-bench-Benchmark, der reale Software-Engineering-Aufgaben in echten Repositories misst (Jimenez et al. 2024, ICLR), stieg die Leistung agentengestützter Systeme von einstelligen Prozentwerten auf über 80%. Claude Code, OpenAIs Codex CLI und vergleichbare Terminal-Agents lösen mehrstufige Aufgaben in strukturierten Repository-Umgebungen zuverlässig. Die Fähigkeit ist da.

Entscheidend ist, was die Benchmarkdaten über die *Ursache* dieser Leistung zeigen. Die SWE-agent-Studie (Yang et al. 2024, NeurIPS) wies nach, dass maßgeschneiderte Agent-Computer-Interfaces (Suchbefehle, interaktives File-Editing mit Linting, Kontextmanagement) die Leistung um das Drei- bis Fünffache gegenüber RAG-Baselines verbesserten, bei identischem Modell. Die Studie formuliert explizit: Die gemessene Leistung eines Agents variiert signifikant mit dem Scaffolding, selbst bei gleichem KI-Modell. Der Confucius Code Agent (Wong et al. 2025, arXiv) bestätigte diesen Befund: Ein schwächeres Modell mit einem starken Agent-Scaffold übertraf ein stärkeres Modell mit einem schwächeren Scaffold.

Gleichzeitig bricht die Leistung ein, wenn die Infrastruktur fehlt. Der Abstand zwischen SWE-bench Verified (~80%) und dem härteren SWE-bench Pro (~23%, Scale AI Labs, 2025), der Agents mit unbekannten Enterprise-Codebasen und weniger strukturierter Dokumentation konfrontiert, beträgt fast 60 Prozentpunkte.

Die resultierende These, die Promptotyping begründet: **Die Zuverlässigkeit agentengestützter Arbeit skaliert nicht mit der Modellfähigkeit allein, sondern mit der Qualität der epistemischen Infrastruktur, in der das Modell operiert.** Die relevante Frage ist nicht "funktionieren Agents?", sondern "unter welchen Bedingungen skaliert ihre Arbeit auf Projektniveau?".

Für das ZBZ-Projekt bedeutet das konkret: Claude Code kann ein TEI-Dokument validieren, visuell mit dem Originalscan abgleichen und korrigieren, nicht weil das Modell besonders gut ist, sondern weil das Repository die nötigen Informationen bereitstellt. Der Agent hat Zugriff auf das RelaxNG-Schema, auf den Entity Index, auf die OCR-Konfiguration und auf die editorischen Richtlinien des Projekts. Ohne diese Infrastruktur würde dasselbe Modell an denselben Dokumenten scheitern.

---

### Epistemische Infrastruktur als Agent-Interface

Ein Promptotyping-Projekt organisiert seine Artifacts in einem Repository. Dieses Repository ist für Agents kein Ablageort, sondern ihr primäres Interface. Agents navigieren die Ordnerstruktur, lesen Knowledge-Dokumente, führen Scripts aus, interpretieren deren Output und treiben damit den nächsten Arbeitsschritt.

Damit ein Repository als epistemische Infrastruktur funktioniert, muss es drei Eigenschaften aufweisen.

**Lesbarkeit.** Jedes Artifact hat einen definierten Zweck, der in einem Kontextdokument beschrieben ist. Agents wissen, was jede Datei tut, ohne sie zuerst analysieren zu müssen. Im ZBZ-Projekt beschreibt `CLAUDE.md` den Projektkontext (Nachlass Jeanne Hersch, Dokumenttypen, Sprachen), die Methodik (Promptotyping, Verarbeitungspipeline) und die verfügbaren Artifacts (Scripts, Indizes, Anwendungen). Diese Anforderung erzeugt einen Wartungsaufwand: Jedes neue Artifact muss in `CLAUDE.md` reflektiert werden. Ohne diese Pflege verliert die Infrastruktur ihre Funktion.

**Konsistenz.** Pfade, Benennungen und Datenformate folgen durchgängigen Konventionen. Im ZBZ-Projekt folgen alle TEI-Dokumente derselben Verzeichnisstruktur, verwenden dieselben Identifikatoren und referenzieren den Entity Index über einheitliche Pfade. Ein Agent, der eine Konvention an einem Dokument gelernt hat, kann sie auf alle 286 Dokumente anwenden.

**Zustandstransparenz.** Der aktuelle Verarbeitungsstand jedes Objekts ist maschinell abfragbar. Im ZBZ-Projekt erzeugen Validierungsscripts JSON-Reports, die den Status jedes Dokuments enthalten (validiert, fehlerhaft, eskaliert). Ein Agent muss den Zustand nicht erschließen, sondern kann ihn lesen.

Diese drei Eigenschaften sind nicht willkürlich gewählt. Sie adressieren empirisch dokumentierte Probleme. Liu et al. (2024, TACL) zeigten, dass Modelle relevante Informationen in der Mitte langer Kontexte systematisch übersehen, was die Bedeutung von Kontextstruktur (Lesbarkeit) unterstreicht. Du et al. (2025, Findings of EMNLP) wiesen nach, dass selbst bei perfektem Retrieval die Leistung mit wachsender Eingabelänge sinkt, was die Bedeutung von Kontextreduktion durch Konsistenz begründet. Zustandstransparenz adressiert den Befund von Gou et al. (2024, ICLR), dass werkzeuggestützte Verifikation (externen Fakten folgen) deutlich zuverlässiger ist als reine Modellinferenz.

`CLAUDE.md` erklärt dem Agent das Warum, `CLAUDE-COMMANDS.md` das Wie. Diese Struktur ist kein Einzelfall. OpenAI implementierte für Codex ein äquivalentes Muster (`AGENTS.md`-Dateien) und formulierte explizit: Wie menschliche Entwickler arbeiten Agenten am besten mit konfigurierten Umgebungen, zuverlässigen Testinfrastrukturen und klarer Dokumentation (OpenAI 2025). Die Konvergenz auf dokumentenbasierte Infrastruktur als Agent-Interface bestätigt das Designprinzip.

---

### Der operative Zyklus

Die Commands strukturieren die Arbeit eines Agents als Zyklus mit fünf Schritten.

**Diagnose.** Der Agent ermittelt den Zustand eines Arbeitsobjekts, indem er die verfügbaren Diagnose-Artifacts ausführt. Im ZBZ-Projekt bedeutet das: Claude Code führt die RelaxNG-Validierung auf einem TEI-Dokument aus und liest den resultierenden Report. Der Report enthält konkrete Fehlermeldungen (fehlende Attribute, ungültige Elementverschachtelungen, inkonsistente Referenzen auf den Entity Index). Der Agent handelt nicht auf Vermutung, sondern auf Befund.

**Exploration.** Der Agent bestimmt, welche Korrekturmaßnahme den größten Qualitätsgewinn verspricht. Im ZBZ-Projekt priorisiert der Agent auf Basis des Validierungsreports: Strukturfehler (fehlende `<div>`-Elemente) vor Referenzfehlern (ungültige Entity-Verweise) vor Formatierungsfragen (Zeilenumbrüche). An diesem Punkt kann der Agent auch feststellen, dass kein bestehendes Artifact das identifizierte Problem löst, und eine Erweiterung vorschlagen.

**Ausführung.** Der Agent ruft das gewählte Artifact auf. Im ZBZ-Projekt korrigiert Claude Code das TEI-Dokument unter Verwendung des Entity Index und der editorischen Richtlinien. Bei Operationen mit API-Kosten (z.B. erneuter LLM-Aufruf für Entity Recognition) nutzt der Agent eine Vorschau-Funktion (`--dry-run`) und bespricht das erwartete Ergebnis mit der DH-Entwicklerin.

**Re-Validierung.** Nach jeder Korrektur führt der Agent die Diagnose erneut aus. Der Vorher-Nachher-Vergleich der Reports bestätigt die Verbesserung und schließt Regressionen aus. Im ZBZ-Projekt bedeutet das: Der Agent zeigt, dass 12 Validierungsfehler auf 3 reduziert wurden und keine neuen Fehler entstanden sind. Dieser Schritt ist nicht optional. Jede Veränderung, die nicht verifiziert wird, ist keine Verbesserung, sondern eine Hypothese.

**Eskalation.** Wenn ein Problem nach einer definierten Anzahl von Iterationen fortbesteht oder wenn der Agent auf ein Fehlermuster stößt, für das kein Artifact existiert, legt der Agent das Problem einem Critical Expert in the Loop vor. Im ZBZ-Projekt geht die Eskalation an die richtige Person: technische Probleme (ein Script schlägt fehl) an die DH-Entwicklerin, fachliche Probleme (eine mehrdeutige Namenszuordnung in einem französischen Brief) an die Editionswissenschaftlerin der ZBZ, Priorisierungsfragen an die Projektleitung.

#### Abbruchbedingungen

Zu frühe Eskalation fragmentiert den Workflow. Zu späte Eskalation verschwendet Rechenressourcen. Promptotyping definiert Abbruchbedingungen auf drei Ebenen: eine maximale Iterationszahl pro Arbeitsobjekt (im ZBZ-Projekt zwei bis drei Zyklen pro Dokument), einen Stagnationsindikator (keine messbare Verbesserung gegenüber dem vorherigen Zyklus) und Fehlermuster-Erkennung (ein Problem, für das kein bestehendes Artifact eine Lösung bietet).

#### Warum dieser Zyklus kein Sonderfall ist

Dieses Muster reflektiert eine konvergente Entwicklung. Das ReAct-Framework (Yao et al. 2023, ICLR) etablierte den Thought → Action → Observation-Loop: "Thought" entspricht Diagnose und Exploration, "Action" der Ausführung, "Observation" der Re-Validierung. Reflexion (Shinn et al. 2023, NeurIPS) erweiterte das Muster um eine explizite Selbstreflexionsschleife und erreichte damit 91% pass@1 auf HumanEval gegenüber 80% bei GPT-4.

Anthropic (2024) identifiziert den Evaluator-Optimizer als zentrales Workflow-Pattern mit iterativem Verfeinerungsloop und menschlichen Checkpoints. Googles Agent Development Kit (2025) implementiert ein `escalate=True`-Signal als architektonisches Primitiv. Dang et al. (2025, arXiv) zeigten, dass bei der Optimierung von Multi-Agent-Orchestrierung durch Reinforcement Learning die entscheidenden Verbesserungen konsistent durch die Emergenz kompakterer, zyklischer Reasoning-Strukturen entstanden. Das zyklische Muster ist kein willkürlicher Designentscheid, sondern eine emergente optimale Struktur.

Promptotyping übernimmt dieses konvergente Muster und konkretisiert es für die Wissensarbeit in den Digital Humanities: Die Diagnose-Artifacts sind projektspezifische Validierungsscripts, die Exploration berücksichtigt Domänenwissen (Dokumenttyp, historischer Kontext, editorische Standards), und die Eskalation adressiert differenzierte Expert-in-the-Loop-Rollen statt eines generischen Feedback-Kanals.

---

### Critical Experts in the Loop

Ein Promptotyping-Projekt hat nicht einen, sondern mehrere Experts in the Loop mit unterschiedlichen Rollen und Kompetenzen. Im ZBZ-Projekt sind das die DH-Entwicklerin (LLM-Infrastruktur und Agent-Konfiguration), die Editionswissenschaftlerin der ZBZ (Domänenwissen, Quellenkenntnis, editorische Standards) und die Projektleitung (Priorisierung und Abnahme).

Die Differenzierung ist nicht nur organisatorisch sinnvoll, sondern epistemisch notwendig. Schroeder, Roy und Kabbara (2025, Findings of ACL) zeigten in einem prä-registrierten Experiment mit 350 Annotatorinnen, dass die Präsentation LLM-generierter Vorschläge die Labelverteilungen der menschlichen Annotatorinnen signifikant verschob. Die Verwendung dieser "menschlich geprüften" Labels zur Evaluation der LLM-Leistung blähte die berichtete Genauigkeit auf. Das Ergebnis ist zirkuläre Validierung: Der Mensch bestätigt, was die Maschine vorschlägt, und die bestätigten Labels gelten als Beweis für die Qualität der Maschine.

Im ZBZ-Projekt adressiert Promptotyping dieses Risiko durch Rollentrennung. Die DH-Entwicklerin konfiguriert den Prozess (welche Prompts, welche Validierungsscripts, welche Schwellenwerte), interagiert aber nicht mit den fachlichen Inhalten. Die Editionswissenschaftlerin bewertet die Ergebnisse, hat aber den Prozess nicht konfiguriert. Die Person, die ein Ergebnis erzeugt hat (oder deren Agent es erzeugt hat), ist nicht dieselbe Person, die es fachlich prüft. Das verhindert den Anchoring-Effekt, den Schroeder et al. dokumentiert haben.

Alle arbeiten mit demselben Repository, denselben Artifacts und denselben Daten. Das Repository ist der gemeinsame Arbeitsraum. Die Artifacts, die der Agent erzeugt (Validierungsreports, Übersichten, kommentierte Fehlerprotokolle), sind gleichzeitig Kommunikationsmittel zwischen den beteiligten Personen. Ein Validierungsreport, den Claude Code für die Re-Validierung erzeugt, ist auch der Report, den die Projektleitung liest, um den Projektstand zu verstehen. Die Eskalationslogik adressiert die richtige Person: technische Probleme an die DH-Entwicklerin, fachliche Probleme an die Editionswissenschaftlerin, Priorisierungsfragen an die Projektleitung.

---

### Agents und Sicherheit

Agents arbeiten innerhalb des versionierten Repository produktiv, nicht destruktiv. Agents erzeugen neue Dateien, aber löschen keine bestehenden. Agents schreiben in Output-Verzeichnisse, aber modifizieren keine Quelldaten. Agents können Scripts ausführen, aber keine Flags verwenden, die bestehende Ergebnisse überschreiben (`--force`), ohne vorherige Freigabe durch einen Expert in the Loop.

Im ZBZ-Projekt bedeutet das: Wenn Claude Code ein TEI-Dokument korrigiert, entsteht eine neue Version neben der bestehenden. Die Originalversion bleibt erhalten. Versionskontrolle (Git) ist die letzte Sicherheitsebene, aber nicht die erste. Die erste ist, dass Agents grundsätzlich additiv arbeiten.

He et al. (MSR 2026) liefern die empirische Begründung: In 806 Projekten, die agentengestützte Coding-Tools ohne systematische Qualitätssicherung einsetzten, stieg die Codekomplexität dauerhaft, während der anfängliche Geschwindigkeitsgewinn nach ein bis zwei Monaten verschwand. Geschwindigkeit ohne Infrastruktur erzeugt technische Schulden. Additive Arbeit ist eine Qualitätssicherungsmaßnahme, die Geschwindigkeitsgewinne nachhaltig macht.

Die unvermeidliche Akkumulation von Dateien erfordert geordnetes Aufräumen. Das ist selbst ein Command: Der Agent erzeugt einen Archivierungsvorschlag, der von einem Expert in the Loop geprüft und freigegeben wird.

---

### Visuelle Verifikation und LLM-as-Judge

Agents mit Vision-Fähigkeit können Arbeitsobjekte visuell prüfen. Im ZBZ-Projekt liest Claude Code den Originalscan eines Briefes und vergleicht ihn mit dem erzeugten TEI-Dokument: Fehlen Absätze? Stimmt die Reihenfolge der Textblöcke? Wurden Strukturelemente (Briefkopf, Datum, Unterschrift) korrekt annotiert? Diese Prüfung geht über Schema-Validierung hinaus, weil sie die inhaltliche Korrektheit betrifft.

Zusätzlich kann der Agent ein zweites Sprachmodell über einen API-Call als unabhängigen Gutachter einsetzen (LLM-as-Judge). Beide Systeme prüfen dasselbe Objekt. Bei übereinstimmender Einschätzung handelt der Agent. Bei abweichender Einschätzung eskaliert er.

Dieses Verfahren adressiert einen zentralen Befund der Selbstkorrektur-Forschung: Kamoi et al. (2024, TACL) zeigten, dass naive Selbstkorrektur (ein Modell prüft seinen eigenen Output ohne externen Feedback) die Leistung verschlechtert. Effektive Selbstkorrektur erfordert externen Feedback, etwa Tool-Ergebnisse, Code-Ausführung oder unabhängige Bewertung. Die Kombination aus Schema-Validierung (formaler Feedback), visueller Verifikation (andere Modalität) und LLM-as-Judge (anderes Modell) erzeugt epistemische Diversität über Verifikationsverfahren, nicht nur über Modelle.

---

### Verifikationskaskade

Jeder Schritt im Zyklus hat Verifikationspunkte. Die Verfahren sind projektspezifisch, aber die Kategorien sind generalisierbar. Ihre Reihenfolge ist nicht beliebig, sondern ökonomisch begründet.

**Automatische Verifikation** prüft formale Korrektheit gegen ein definiertes Schema oder Regelwerk. Das Ergebnis ist binär und maschinell auswertbar. Im ZBZ-Projekt: RelaxNG-Validierung eines TEI-Dokuments. Günstig, schnell, filtert offensichtliche Fehler.

**Kontextuelle Verifikation** prüft inhaltliche Plausibilität unter Einbeziehung von Projektkontext. Das Ergebnis ist graduell (plausibel, fraglich, unplausibel). Im ZBZ-Projekt: Der Agent prüft, ob die erkannten Entities mit dem bekannten Thema des Dokuments konsistent sind. Ein Brief aus Genf, der ausschließlich Entities in Brasilien enthält, ist auffällig.

**Visuelle Verifikation** prüft Übereinstimmung zwischen Arbeitsergebnis und Quelle. Im ZBZ-Projekt: Abgleich des TEI-Texts gegen den Originalscan durch Claude Code oder einen LLM-as-Judge.

**Fachliche Verifikation** prüft editorische, historische oder domänenspezifische Korrektheit. Kann nicht an Agents delegiert werden. Im ZBZ-Projekt: Die Editionswissenschaftlerin der ZBZ entscheidet, ob eine mehrdeutige Namenszuordnung in einem handschriftlichen französischen Brief korrekt aufgelöst wurde.

Automatische Verifikation steht am Anfang. Fachliche Verifikation steht am Ende. Der Zyklus reduziert systematisch die Menge an Fällen, die fachliche Verifikation erfordern. Das ist die operative Bedeutung von **asymmetrischer Amplifikation**: Die automatisierbaren Schritte verstärken die Wirkung der menschlichen Expertise, indem sie die Fachexpertinnen auf die tatsächlich schwierigen Fälle konzentrieren. Der menschliche Aufwand wird nicht ersetzt, sondern auf seinen höchstwertigen Einsatzbereich fokussiert.

#### Agent-Based Quality Screening als Verifikationskaskade in der Praxis

Im ZBZ-Projekt wurde die Verifikationskaskade als operativer Prozess erprobt: ein Agent-Based Quality Screening, bei dem Claude Code fünf TEI-Dokumente unterschiedlicher Sprache, Gattung und Komplexität systematisch prüft. Der Prozess durchläuft sieben Schichten: Scan-Qualität, OCR-Treue, Layout-Korrektheit, TEI-Struktur (Schema-Validierung), Referenz-Vergleich (wo ZBZ-Referenz-TEI vorliegt), Entity-Plausibilität und Gesamtkohärenz. Pro Dokument entsteht ein maschinenlesbarer Befund (Review-JSON), über alle Dokumente eine Muster-Analyse (Sweep-Summary).

Die Ergebnisse zeigen, wie die Kaskade in der Praxis funktioniert. Die automatische Verifikation (RelaxNG-Validierung) bestätigte alle fünf Dokumente als schema-valide und filterte formale Fehler aus 284 von 285 Dokumenten des Gesamtkorpus heraus. Die kontextuelle Verifikation identifizierte sechs systematische Muster, darunter: Entity-Typ-Konflikte bei Personen, deren Namen auch Werktitel sind (Kierkegaard, Nietzsche — im Entity Index sowohl als Person als auch als Werk geführt), und eine inhaltlich erklärbare Schieflage bei abstrakten philosophischen Texten, die weniger Entities enthalten als biographische. Die visuelle Verifikation deckte auf, dass Doppelseiten-Scans aus Buchformaten technisch korrekte, aber optisch unerwartete Layout-Strukturen erzeugen, und dass Gemini im TEI-Erzeugungsschritt nebenbei OCR-Fehler korrigiert (ein undokumentierter Qualitätsgewinn, der nur durch Vergleich von Roh-OCR und finalem TEI-Text sichtbar wird).

Die fachliche Verifikation steht noch aus: Die Editionswissenschaftlerin der ZBZ wird dieselben fünf Dokumente im Curation Editor prüfen. Erst dieser Vergleich — was hat der Agent gefunden, was hat die Fachexpertin gefunden, was haben beide übersehen — liefert die empirische Basis für die Evaluation der Kaskade. Das Screening ist als Pre-Curation-Prozess positioniert: Es erzeugt vorgeprüfte Dokumente mit strukturiertem Befund, nicht fertige Editionen. Der Agent reduziert die Menge an Dokumenten, die fachliche Aufmerksamkeit erfordern, und fokussiert die menschliche Expertise auf die tatsächlich schwierigen Fälle.

---

### Artifacts als rückgekoppelter Output

Promptotyping Artifacts haben eine Eigenschaft, die sie von gewöhnlichen Arbeitsergebnissen unterscheidet: Sie sind gleichzeitig Output des Prozesses und Input für den nächsten Zyklus.

Im ZBZ-Projekt zeigt sich dieser Mechanismus an drei Stellen. Erstens wird der Entity Index, der in einem frühen Durchlauf aus 50 Dokumenten erzeugt wurde, zum Kontextwissen für die Verarbeitung der nächsten 50 Dokumente. Der Agent erkennt Entities besser, weil er bereits weiß, welche Personen, Orte und Institutionen im Nachlass vorkommen. Zweitens führt ein Validierungsreport, der ein wiederkehrendes Fehlermuster dokumentiert (etwa falsch erkannte Briefdaten bei einem bestimmten Handschriftentyp), zur Erweiterung eines Scripts, das als neues Artifact in den Zyklus eintritt. Drittens erzeugt der Curation Editor, der als Werkzeug für die Editionswissenschaftlerin gebaut wurde, kuratierte Daten, die als Qualitätsbeispiele für die nächste Iteration der automatischen Verarbeitung dienen können.

Dieser Mechanismus ist keine Rekursion (kein Artifact ruft sich selbst auf), sondern iterative Rückkopplung. Jeder Durchlauf hinterlässt Artifacts, die den nächsten Durchlauf informieren und verbessern. Die epistemische Infrastruktur wächst mit dem Projekt. Das Repository am Ende des Projekts ist nicht dasselbe wie am Anfang, nicht nur weil es mehr Daten enthält, sondern weil es mehr Werkzeuge, mehr Kontextwissen und mehr Verarbeitungskapazität hat.

Zhang et al. (2025/2026, arXiv) beschreiben mit Agentic Context Engineering (ACE) ein formales Modell für diesen Prozess: Kontexte werden als akkumulierende Strategiedokumente behandelt. Auf dem AppWorld-Leaderboard erreichte ACE mit einem kleineren Open-Source-Modell die Leistung des bestplatzierten Produktionsagenten. Akkumuliertes Kontextwissen kompensiert Modellfähigkeit. Das ist exakt der Mechanismus, den Promptotyping über die Rückkopplung der Artifacts realisiert.

---

### Prospektives Evaluationsdesign

Die Promptotyping-Methodik definiert ihre eigenen Erfolgskriterien und macht sich daran überprüfbar. Drei Dimensionen bilden das Evaluationsdesign, das im Lauf des ZBZ-Projekts mit Daten befüllt wird.

**Eskalationsrate pro Zyklus.** Der Anteil der Dokumente, die nach dem automatischen Zyklus noch fachliche Verifikation durch die Editionswissenschaftlerin erfordern. Wenn die Rückkopplungslogik funktioniert (der wachsende Entity Index, verbesserte Scripts, akkumulierte Erfahrungen), sollte diese Rate über die Dokumentchargen sinken. Ein stabiler oder steigender Trend würde darauf hindeuten, dass die epistemische Infrastruktur nicht wächst oder nicht genutzt wird.

Erste Daten aus dem ZBZ-Projekt: Von 285 verarbeiteten Dokumenten sind 284 schema-valide (99,6%). Das Agent-Based Quality Screening der fünf Pilotdokumente ergab null Eskalationen an die Fachexpertin — alle fünf wurden als APPROVED_WITH_NOTES bewertet. Die sechs identifizierten systematischen Muster (Entity-Typ-Konflikte, Doppelseiten-Scans, JSTOR-Scope-Probleme) betreffen Pipeline-Verbesserungen, nicht fachliche Entscheidungen. Diese Zahlen sind ein Ausgangswert. Die entscheidende Messung folgt, wenn die Editionswissenschaftlerin der ZBZ dieselben fünf Dokumente prüft: Welche Probleme findet sie, die der Agent übersehen hat?

**Artifact-Landschaft.** Welche neuen Scripts, Indizes oder Kontextdokumente entstehen im Lauf des Projekts? Wie verändern sie den Zyklus?

Im ZBZ-Projekt lässt sich die Artifact-Landschaft über die Projektlaufzeit (29. Januar bis 15. März 2026) dokumentieren. Das Repository begann mit einem OCR-Script und einem Evaluations-Dashboard. Sieben Wochen später umfasst es 14 Knowledge-Dokumente, 7 NER-Module, einen TEI-Validator mit 8 Projektregeln und 11 Warnungen, einen Entity Index mit 4.100 Einträgen, einen Curation Editor und ein Agent-Based Quality Screening mit maschinenlesbaren Review-JSONs. Jedes dieser Artifacts entstand als Antwort auf ein konkretes Problem: Der Validator entstand, weil die ersten TEI-Dokumente Schema-Fehler hatten. Die Stopwort-Liste für Entities entstand, weil generische Begriffe ("Dieu", "suisse") als Entitäten markiert wurden. Das Quality Screening entstand, weil die automatische Validierung allein nicht ausreichte, um die inhaltliche Korrektheit zu beurteilen. Die Artifact-Landschaft wächst nicht additiv, sondern reaktiv auf Qualitätssignale.

**Verteilung menschlicher Aufmerksamkeit.** Wofür wendet die Editionswissenschaftlerin der ZBZ tatsächlich ihre Zeit auf? Wenn die Verifikationskaskade funktioniert, sollte sich ihre Arbeit auf fachlich schwierige Fälle konzentrieren (mehrdeutige Namenszuordnungen, unlesbare Passagen, editorische Grundsatzentscheidungen), nicht auf Formatkorrekturen oder Schemavalidierung. Eine Verschiebung der Aufmerksamkeit von Routineaufgaben zu Expertinnenaufgaben über die Projektlaufzeit würde die These der asymmetrischen Amplifikation empirisch belegen.

Diese Dimension ist noch nicht messbar — sie erfordert den Kurationspilot mit der ZBZ. Die Review-JSONs aus dem Quality Screening liefern jedoch eine Baseline: Sie dokumentieren, welche Fragen der Agent nicht beantworten konnte und an die Fachexpertin weitergibt. Im Pilotdurchlauf waren das: die korrekte Zuordnung mehrdeutiger Entity-Namen (Kierkegaard als Person oder Werk?), die editorische Bewertung von Copyright-Zeilen im TEI und die Frage, ob JSTOR-Coverseiten Teil des edierten Texts sind. Diese Fragen sind genau die Art von Expertinnenaufgaben, auf die die Kaskade hinarbeitet.

Diese drei Dimensionen liefern keine einzelne Kennzahl, sondern ein trianguliertes Bild. Gemeinsam zeigen sie, ob Promptotyping seinen eigenen Anspruch einlöst: dass die epistemische Infrastruktur wächst, dass diese Infrastruktur die Agentarbeit verbessert und dass menschliche Expertise dort eingesetzt wird, wo sie den größten Wertbeitrag leistet. Die ersten Daten aus dem ZBZ-Projekt sind konsistent mit diesen Thesen, aber noch nicht hinreichend: Die entscheidende Prüfung ist der Vergleich zwischen Agent-Befund und Fach-Befund im Kurationspilot.

---

### Literatur

#### Peer-reviewed

Dang et al. (2025). Multi-Agent Collaboration via Evolving Orchestration. arXiv 2505.19591.

Du, Tian, Ronanki et al. (2025). Context Length Alone Hurts LLM Performance Despite Perfect Retrieval. *Findings of EMNLP 2025*, 23281–23298.

Gou, Shao, Gong et al. (2024). CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing. *ICLR 2024*.

He, Miller, Agarwal, Kästner, Vasilescu (2026). Speed at the Cost of Quality. *MSR 2026*.

Jimenez, Yang, Wettig et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*.

Kamoi, Zhang, Zhang, Han, Zhang (2024). When Can LLMs Actually Correct Their Own Mistakes? *TACL*, 12, 1417–1440.

Liu, Lin, Hewitt et al. (2024). Lost in the Middle: How Language Models Use Long Contexts. *TACL*, 12, 157–173.

Schroeder, Roy, Kabbara (2025). Just Put a Human in the Loop? *Findings of ACL 2025*.

Shinn, Cassano, Gopinath, Narasimhan, Yao (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*.

Yang, Jimenez, Zhang, Lieret et al. (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. *NeurIPS 2024*.

Yao, Zhao, Yu et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.

#### Preprints und technische Berichte

Anthropic (2024). Building Effective Agents. anthropic.com/research.

Google (2025). Developer's Guide to Multi-Agent Patterns in ADK. Google Developers Blog.

OpenAI (2025). Introducing Codex. openai.com.

Wong, Qi et al. (2025). Confucius Code Agent. arXiv 2512.10398.

Zhang et al. (2025/2026). Agentic Context Engineering (ACE). arXiv 2510.04618.