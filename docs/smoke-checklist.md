# Smoke-Checkliste: Live View mit dem Vorlesungs-Demo

Automatische Tests prüfen nur das Modell der Live View. Ob die Animationen flüssig
laufen, die Farben auf dem Beamer funktionieren und alles verständlich ist, lässt sich
nur von Hand prüfen. Diese Liste geht das Demo-Skript Schritt für Schritt durch; die
Abschnitte und Schritt-Namen entsprechen den Kapiteln (`=== … ===`) und Erklärungen,
die `git-visualizer-demo` ausgibt.

Am besten auf dem echten Beamer bzw. in einem Fenster in Beamergröße (mindestens
1920×1080), aus der hintersten Reihe betrachtet.

## Vorbereitung

```sh
git-visualizer-demo --live-view     # startet Demo und Live View zusammen
# oder: git-visualizer-demo  und den ausgegebenen Befehl
#       git-visualizer /tmp/git-visualizer-demo-…/vorlesung  in einem zweiten Terminal
```

Das Skript legt alles in einem neuen temporären Ordner an (`vorlesung`, `server.git`,
`kollegin`) und fasst kein anderes Repository an. Vor jedem Schritt zeigt es die
Erklärung und die git-Befehle und wartet auf Enter; `q` beendet. Unter „→ Live View:“
steht, was zu sehen sein sollte. Am Ende bleibt der Ordner erhalten (der
`rm -rf`-Befehl zum Aufräumen wird ausgegeben).

- [x] Fenster ohne Werkzeugleisten und Buttons; Titel „Git Visualizer“
- [x] Vor Schritt 1: „Kein Repository – warte auf `git init`“
- [x] `git-visualizer` ohne Pfad gestartet zeigt die Ordnerauswahl („Ordner für die Live View wählen“) – einmal separat prüfen

## 1. Repository anlegen

- [x] **init**: Der Wartehinweis verschwindet ohne Neustart, die leere Ansicht mit „Working Tree“ und „Staging Bereich“ erscheint (innerhalb einer Sekunde)

## 2. Commits

- [x] **first-file**: README.md erscheint im Working Tree mit Badge „unversioniert“ (eingeblendet, nicht hart)
- [x] **first-add**: README.md *gleitet* vom Working Tree in den Staging Bereich, Badge „neu“
- [x] **first-commit**: README.md *fliegt* aus dem Staging Bereich in den Commit-Knoten; erst danach *wächst* der Commit ein
- [x] Commit-Knoten: kurzer Hash klein, erste Zeile der Nachricht groß, gut lesbar; Knoten sehen gepflegt aus (offen aus Ticket 03)
- [x] Label main mit eigenem HEAD-Marker darüber; der HEAD-Commit ist hervorgehoben
- [x] **second-commit**: Neuer Commit rechts daneben; main und HEAD *gleiten* mit, statt zu springen

## 3. Staging Bereich

- [x] **modify**: README.md im Working Tree mit „geändert“
- [x] **stage-modified**: README.md gleitet in den Staging Bereich
- [x] **partial-staging**: README.md steht in *beiden* Spalten
- [x] **unstage**: README.md gleitet *zurück* in den Working Tree (umgekehrte Bewegung), danach nur noch dort
- [x] **commit-all**: README.md fliegt in den neuen Commit
- [x] Die Reihenfolge Datei-Flug → Commit wächst ein → Labels gleiten liest sich auf dem Beamer klar (offen aus Ticket 06)

## 4. Branches

- [x] **branch**: Label feature erscheint am selben Commit wie main, beide Labels gestapelt und lesbar; HEAD gleitet von main zu feature
- [x] **feature-commit**: feature bekommt eine eigene, stabile Farbe; nur feature + HEAD rücken vor, main bleibt
- [x] **switch-main**: HEAD gleitet zurück zu main
- [x] Farben der Branches bleiben über alle weiteren Schritte gleich

## 5. Merge

- [x] **fast-forward**: main (mit HEAD) gleitet nach vorn zu feature – kein neuer Commit wächst ein
- [x] **delete-merged-branch**: Label feature *blendet aus*; alle Commits bleiben normal sichtbar (keine Ghost Commits)
- [x] **diverge**: Die History verzweigt sich, login hat eine eigene Spur in eigener Farbe
- [x] **three-way-merge**: Merge-Commit wächst ein, mit Kanten zu *beiden* Eltern; unterscheidet sich deutlich vom Fast-forward
- [x] Spalten nach Abstammung: jeder Commit eine Spalte rechts vom neuesten Elternteil

## 6. Merge-Konflikt

- [x] **conflict-setup**: Zwei neue Spitzen (farbe, main)
- [x] **conflict**: Banner „Merge läuft – 1 Konflikt“ blendet ein, rot; config.txt im Working Tree mit rotem Rahmen und Badge „Konflikt“
- [x] **resolve**: config.txt gleitet in den Staging Bereich; Banner wird gelb/amber: „Merge läuft – keine Konflikte mehr“
- [x] **conclude-merge**: Merge-Commit wächst ein, Banner blendet aus

## 7. Ghost Commits

- [x] **typo-commit**: Neuer Commit „Notizen“
- [x] **amend**: Der Commit „Notizen (korrigiert)“ wächst ein; „Notizen“ bleibt *blass* an seinem Platz als Ghost Commit (mit blassen Kanten)
- [x] **rebase-setup**: Der Ghost Commit verschwindet, sobald sich eine Ref bewegt
- [x] **rebase**: Zwei Kopien wachsen hinter main ein, experiment + HEAD gleiten hin; die Originale bleiben blass stehen; nichts anderes verrutscht
- [x] **clear-ghosts**: `Esc` in der Live View blendet die Ghost Commits aus
- [x] **rebase-conflict**: Banner „Rebase 1/3 – 1 Konflikt“; HEAD sitzt *losgelöst* direkt am Commit (umrandet, nicht über einem Branch-Label); experiment.txt mit rotem Konflikt-Rahmen
- [x] **rebase-abort**: Banner blendet aus, HEAD hängt wieder an experiment
- [x] **delete-unmerged-branch**: HEAD gleitet zu main; Label experiment blendet aus, seine drei Commits werden Ghost Commits
- [x] Nach einem Neustart der Live View gibt es keine Ghost Commits

## 8. Remote

- [x] **remote-create**: Rechts neben der History erscheint die Remote-Box „origin“ mit gekürzter URL, „noch nie geholt“
- [x] **push-upstream**: Umrandetes Label origin/main in der Farbe von main; main zeigt `↑0 ↓0`; in der Box erscheint origin/main; weiterhin „noch nie geholt“ (ein Push ist kein Holen)
- [x] **local-ahead**: main zeigt `↑1 ↓0`, origin/main bleibt stehen
- [x] **push**: origin/main gleitet zu main, `↑0 ↓0`
- [x] **colleague-pushes**: In der Live View ändert sich *nichts* (sie fragt den Server nie)
- [x] **fetch**: Der Commit der Kollegin erscheint in der History, origin/main gleitet hin; main zeigt `↑0 ↓1`; Box: „zuletzt geholt gerade eben“ (nach einer Minute „vor 1 Min.“)
- [x] **diverged**: main zeigt `↑1 ↓1`
- [x] **pull**: Merge-Commit wächst ein; `↑2 ↓0`
- [x] **push-merged**: origin/main gleitet zu main, `↑0 ↓0`
- [x] **push-without-upstream**: origin/neu erscheint (grau umrandet, nicht in der Farbe von neu); neu zeigt *keinen* ↑/↓-Zähler
- [x] **set-upstream**: neu zeigt `↑0 ↓0`, origin/neu nimmt die Farbe von neu an

## Zoom und Auto-Fit

Am besten am Ende des Demos, wenn die History voll ist.

- [x] Während des ganzen Demos passt sich die History dem Fenster an; die neuesten Commits und die Remote-Box bleiben sichtbar
- [x] Fenster verkleinern/vergrößern: History passt sich an, neueste Commits bleiben sichtbar
- [x] `Strg +` vergrößert, `Strg −` verkleinert, `Strg 0` stellt die Originalgröße wieder her; History und Three Areas skalieren mit (feste Pixelwerte außerhalb von `Theme` zoomen noch nicht, siehe Ticket 10)
- [x] `git-visualizer --max-commits 5 …/vorlesung`: nur die fünf neuesten Commits, ältere als „…“ zusammengefasst

## Designs

- [x] Start im hellen Design
- [x] `T` schaltet auf dunkel und zurück, ohne Neustart
- [x] In *beiden* Designs gut lesbar (auch auf dem Beamer): Branch-Farben, umrandete Remote-tracking-Labels, ↑/↓-Zähler, Ghost Commits (blass, aber erkennbar), rotes und gelbes Banner, roter Konflikt-Rahmen, Datei-Badges, Remote-Box, Tastenkürzel-Übersicht und Legende

## Legende

- [x] `L` blendet die Legende ein und wieder aus
- [x] Sie erklärt mit denselben Elementen wie die Live View (keine Screenshots): HEAD-Marker (an einem Branch / losgelöst), Branch-Label und umrandetes Remote-tracking-Label, ↑/↓-Zähler, Ghost Commit, Konflikt-Markierung, Banner einer laufenden Operation, Änderungsarten im Working Tree / Staging Bereich
- [x] Sie folgt dem Design (`T` bei offener Legende)
- [x] Text auf Deutsch mit den Vorlesungsbegriffen („Staging Bereich“, Branch, Commit, HEAD …)

## Tastenkürzel-Übersicht

- [x] `?` blendet die Übersicht „Tastenkürzel“ ein und wieder aus
- [x] Sie listet alle Kürzel: `Strg +`, `Strg −`, `Strg 0`, `Esc`, `T`, `L`, `?`
- [x] Jedes gelistete Kürzel funktioniert wirklich

## Extras (von Hand im Demo-Repository)

Diese Fälle deckt das Skript nicht ab; im `vorlesung`-Ordner eintippen.

- [x] `git tag v1`: graues Tag-Label am Commit
- [x] `echo x >> README.md && git stash`: keine Stash-Commits in der History
- [x] `git switch --detach HEAD~1`: HEAD losgelöst am Commit; `git switch neu` hängt ihn wieder an (HEAD gleitet)
- [x] `F5` liest das Repository neu ein (versteckter Notbehelf, nicht in der Übersicht)

## Gesamteindruck

- [x] Alle Animationen laufen auf dem Beamer flüssig, ohne Flackern oder Zwischenzustände (offen aus Ticket 05)
- [x] Alle sichtbaren Texte sind deutsch, git-Begriffe im Original (offen aus Ticket 10)
- [x] Die Live View hat nie selbst etwas am Repository geändert (`git status` im Terminal zeigt nur, was das Skript getan hat)
