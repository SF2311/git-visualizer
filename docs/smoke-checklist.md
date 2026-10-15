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

- [ ] Fenster ohne Werkzeugleisten und Buttons; Titel „Git Visualizer“
- [ ] Vor Schritt 1: „Kein Repository – warte auf `git init`“
- [ ] `git-visualizer` ohne Pfad gestartet zeigt die Ordnerauswahl („Ordner für die Live View wählen“) – einmal separat prüfen

## 1. Repository anlegen

- [ ] **init**: Der Wartehinweis verschwindet ohne Neustart, die leere Ansicht mit „Working Tree“ und „Staging Bereich“ erscheint (innerhalb einer Sekunde)

## 2. Commits

- [ ] **first-file**: README.md erscheint im Working Tree mit Badge „untracked“ (eingeblendet, nicht hart)
- [ ] **first-add**: README.md *gleitet* vom Working Tree in den Staging Bereich, Badge „neu“
- [ ] **first-commit**: README.md *fliegt* aus dem Staging Bereich in den Commit-Knoten; erst danach *wächst* der Commit ein
- [ ] Commit-Knoten: kurzer Hash klein, erste Zeile der Nachricht groß, gut lesbar; Knoten sehen gepflegt aus (offen aus Ticket 03)
- [ ] Label main mit eigenem HEAD-Marker darüber; der HEAD-Commit ist hervorgehoben
- [ ] **second-commit**: Neuer Commit rechts daneben; main und HEAD *gleiten* mit, statt zu springen

## 3. Staging Bereich

- [ ] **modify**: README.md im Working Tree mit „geändert“
- [ ] **stage-modified**: README.md gleitet in den Staging Bereich
- [ ] **partial-staging**: README.md steht in *beiden* Spalten
- [ ] **unstage**: README.md gleitet *zurück* in den Working Tree (umgekehrte Bewegung), danach nur noch dort
- [ ] **commit-all**: README.md fliegt in den neuen Commit
- [ ] Die Reihenfolge Datei-Flug → Commit wächst ein → Labels gleiten liest sich auf dem Beamer klar (offen aus Ticket 06)

## 4. Branches

- [ ] **branch**: Label feature erscheint am selben Commit wie main, beide Labels gestapelt und lesbar; HEAD gleitet von main zu feature
- [ ] **feature-commit**: feature bekommt eine eigene, stabile Farbe; nur feature + HEAD rücken vor, main bleibt
- [ ] **switch-main**: HEAD gleitet zurück zu main
- [ ] Farben der Branches bleiben über alle weiteren Schritte gleich

## 5. Merge

- [ ] **fast-forward**: main (mit HEAD) gleitet nach vorn zu feature – kein neuer Commit wächst ein
- [ ] **delete-merged-branch**: Label feature *blendet aus*; alle Commits bleiben normal sichtbar (keine Ghost Commits)
- [ ] **diverge**: Die History verzweigt sich, login hat eine eigene Spur in eigener Farbe
- [ ] **three-way-merge**: Merge-Commit wächst ein, mit Kanten zu *beiden* Eltern; unterscheidet sich deutlich vom Fast-forward
- [ ] Spalten nach Abstammung: jeder Commit eine Spalte rechts vom neuesten Elternteil

## 6. Merge-Konflikt

- [ ] **conflict-setup**: Zwei neue Spitzen (farbe, main)
- [ ] **conflict**: Banner „Merge läuft – 1 Konflikt“ blendet ein, rot; config.txt im Working Tree mit rotem Rahmen und Badge „Konflikt“
- [ ] **resolve**: config.txt gleitet in den Staging Bereich; Banner wird gelb/amber: „Merge läuft – keine Konflikte mehr“
- [ ] **conclude-merge**: Merge-Commit wächst ein, Banner blendet aus

## 7. Ghost Commits

- [ ] **typo-commit**: Neuer Commit „Notizen“
- [ ] **amend**: Der Commit „Notizen (korrigiert)“ wächst ein; „Notizen“ bleibt *blass* an seinem Platz als Ghost Commit (mit blassen Kanten)
- [ ] **rebase-setup**: Der Ghost Commit verschwindet, sobald sich eine Ref bewegt
- [ ] **rebase**: Zwei Kopien wachsen hinter main ein, experiment + HEAD gleiten hin; die Originale bleiben blass stehen; nichts anderes verrutscht
- [ ] **clear-ghosts**: `Esc` in der Live View blendet die Ghost Commits aus
- [ ] **rebase-conflict**: Banner „Rebase 1/3 – 1 Konflikt“; HEAD sitzt *losgelöst* direkt am Commit (umrandet, nicht über einem Branch-Label); experiment.txt mit rotem Konflikt-Rahmen
- [ ] **rebase-abort**: Banner blendet aus, HEAD hängt wieder an experiment
- [ ] **delete-unmerged-branch**: HEAD gleitet zu main; Label experiment blendet aus, seine drei Commits werden Ghost Commits
- [ ] Nach einem Neustart der Live View gibt es keine Ghost Commits

## 8. Remote

- [ ] **remote-create**: Rechts neben der History erscheint die Remote-Box „origin“ mit gekürzter URL, „noch nie geholt“
- [ ] **push-upstream**: Umrandetes Label origin/main in der Farbe von main; main zeigt `↑0 ↓0`; in der Box erscheint origin/main; weiterhin „noch nie geholt“ (ein Push ist kein Holen)
- [ ] **local-ahead**: main zeigt `↑1 ↓0`, origin/main bleibt stehen
- [ ] **push**: origin/main gleitet zu main, `↑0 ↓0`
- [ ] **colleague-pushes**: In der Live View ändert sich *nichts* (sie fragt den Server nie)
- [ ] **fetch**: Der Commit der Kollegin erscheint in der History, origin/main gleitet hin; main zeigt `↑0 ↓1`; Box: „zuletzt geholt gerade eben“ (nach einer Minute „vor 1 Min.“)
- [ ] **diverged**: main zeigt `↑1 ↓1`
- [ ] **pull**: Merge-Commit wächst ein; `↑2 ↓0`
- [ ] **push-merged**: origin/main gleitet zu main, `↑0 ↓0`
- [ ] **push-without-upstream**: origin/neu erscheint (grau umrandet, nicht in der Farbe von neu); neu zeigt *keinen* ↑/↓-Zähler
- [ ] **set-upstream**: neu zeigt `↑0 ↓0`, origin/neu nimmt die Farbe von neu an

## Zoom und Auto-Fit

Am besten am Ende des Demos, wenn die History voll ist.

- [ ] Während des ganzen Demos passt sich die History dem Fenster an; die neuesten Commits und die Remote-Box bleiben sichtbar
- [ ] Fenster verkleinern/vergrößern: History passt sich an, neueste Commits bleiben sichtbar
- [ ] `Strg +` vergrößert, `Strg −` verkleinert, `Strg 0` stellt die Originalgröße wieder her; History und Three Areas skalieren mit (feste Pixelwerte außerhalb von `Theme` zoomen noch nicht, siehe Ticket 10)
- [ ] `git-visualizer --max-commits 5 …/vorlesung`: nur die fünf neuesten Commits, ältere als „…“ zusammengefasst

## Designs

- [ ] Start im hellen Design
- [ ] `T` schaltet auf dunkel und zurück, ohne Neustart
- [ ] In *beiden* Designs gut lesbar (auch auf dem Beamer): Branch-Farben, umrandete Remote-tracking-Labels, ↑/↓-Zähler, Ghost Commits (blass, aber erkennbar), rotes und gelbes Banner, roter Konflikt-Rahmen, Datei-Badges, Remote-Box, Tastenkürzel-Übersicht und Legende

## Legende

- [ ] `L` blendet die Legende ein und wieder aus
- [ ] Sie erklärt mit denselben Elementen wie die Live View (keine Screenshots): HEAD-Marker (an einem Branch / losgelöst), Branch-Label und umrandetes Remote-tracking-Label, ↑/↓-Zähler, Ghost Commit, Konflikt-Markierung, Banner einer laufenden Operation, Änderungsarten im Working Tree / Staging Bereich
- [ ] Sie folgt dem Design (`T` bei offener Legende)
- [ ] Text auf Deutsch mit den Vorlesungsbegriffen („Staging Bereich“, Branch, Commit, HEAD …)

## Tastenkürzel-Übersicht

- [ ] `?` blendet die Übersicht „Tastenkürzel“ ein und wieder aus
- [ ] Sie listet alle Kürzel: `Strg +`, `Strg −`, `Strg 0`, `Esc`, `T`, `L`, `?`
- [ ] Jedes gelistete Kürzel funktioniert wirklich

## Extras (von Hand im Demo-Repository)

Diese Fälle deckt das Skript nicht ab; im `vorlesung`-Ordner eintippen.

- [ ] `git tag v1`: graues Tag-Label am Commit
- [ ] `echo x >> README.md && git stash`: keine Stash-Commits in der History
- [ ] `git switch --detach HEAD~1`: HEAD losgelöst am Commit; `git switch neu` hängt ihn wieder an (HEAD gleitet)
- [ ] `F5` liest das Repository neu ein (versteckter Notbehelf, nicht in der Übersicht)

## Gesamteindruck

- [ ] Alle Animationen laufen auf dem Beamer flüssig, ohne Flackern oder Zwischenzustände (offen aus Ticket 05)
- [ ] Alle sichtbaren Texte sind deutsch, git-Begriffe im Original (offen aus Ticket 10)
- [ ] Die Live View hat nie selbst etwas am Repository geändert (`git status` im Terminal zeigt nur, was das Skript getan hat)
