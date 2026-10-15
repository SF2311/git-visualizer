"""Lecture demo: walks a fresh repository through a typical git lecture, step by step.

``git-visualizer-demo`` creates a new temporary folder and, inside it only, the
Observed Repository ``vorlesung``, a bare Remote ``server.git`` and a second clone
``kollegin`` (a colleague who pushes). Every step prints a short German explanation and
the exact commands, waits for Enter and then runs them with real git, so the Live View
on ``vorlesung`` can be watched animating each change. See ``docs/smoke-checklist.md``.

The demo refuses to run a command whose working directory or path arguments lie
outside its temporary folder, stops git from discovering repositories above it, and
ignores the lecturer's global git configuration so that every run behaves the same.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

OBSERVED = "vorlesung"
"""The Observed Repository, relative to the demo folder."""
REMOTE = "server.git"
COLLEAGUE = "kollegin"


class OutsideDemoFolderError(RuntimeError):
    """A command would run in, or name a path in, a place outside the demo folder."""


@dataclass(frozen=True)
class Git:
    """``git <args>``, run in the Observed Repository. ``fails`` marks an expected error."""

    args: tuple[str, ...]
    fails: bool = False

    def shown(self) -> str:
        return shlex.join(("git", *self.args))


@dataclass(frozen=True)
class Write:
    """Write (or with ``append`` add) one line to a file, shown as ``echo``."""

    path: str
    line: str
    append: bool = False

    def shown(self) -> str:
        return f"echo {shlex.quote(self.line)} {'>>' if self.append else '>'} {shlex.quote(self.path)}"


Action = Git | Write


@dataclass(frozen=True)
class Step:
    """One pause of the demo: an explanation, then commands run after Enter.

    ``live_view_key`` names a key the lecturer presses in the Live View instead of
    running a command (e.g. ``Esc``); tests simulate it on the model.
    """

    id: str
    chapter: str
    explanation: str
    actions: tuple[Action, ...] = ()
    live_view_key: str | None = None
    watch: str = ""


def git(*args: str, fails: bool = False) -> Git:
    return Git(tuple(args), fails)


def _steps() -> tuple[Step, ...]:
    colleague = f"../{COLLEAGUE}"
    return (
        # --- 1. init -------------------------------------------------------------
        Step(
            "init",
            "Repository anlegen",
            "Aus dem leeren Ordner wird ein git-Repository.",
            (git("init", "-b", "main"),),
            watch="„Kein Repository – warte auf git init“ verschwindet, die leere Ansicht erscheint.",
        ),
        # --- 2. commits ----------------------------------------------------------
        Step(
            "first-file",
            "Commits",
            "Eine neue Datei liegt nur im Working Tree – git kennt sie noch nicht.",
            (Write("README.md", "# Vorlesung git"),),
            watch="README.md erscheint im Working Tree als „untracked“.",
        ),
        Step(
            "first-add",
            "Commits",
            "`git add` legt eine Kopie der Datei in den Staging Bereich.",
            (git("add", "README.md"),),
            watch="README.md gleitet vom Working Tree in den Staging Bereich („neu“).",
        ),
        Step(
            "first-commit",
            "Commits",
            "`git commit` speichert den Staging Bereich als ersten Commit.",
            (git("commit", "-m", "README anlegen"),),
            watch="README.md fliegt in den neuen Commit, der dann einwächst; main und HEAD erscheinen.",
        ),
        Step(
            "second-commit",
            "Commits",
            "Noch ein Commit: neue Datei anlegen, stagen, committen.",
            (
                Write("hallo.py", "print('Hallo')"),
                git("add", "hallo.py"),
                git("commit", "-m", "Hallo-Skript"),
            ),
            watch="Neuer Commit rechts vom ersten; main und HEAD gleiten mit.",
        ),
        # --- 3. add / partial staging ------------------------------------------
        Step(
            "modify",
            "Staging Bereich",
            "Eine Datei ändern: die Änderung ist zunächst nur im Working Tree.",
            (Write("README.md", "Kapitel 1: Commits", append=True),),
            watch="README.md erscheint im Working Tree als „geändert“.",
        ),
        Step(
            "stage-modified",
            "Staging Bereich",
            "Die Änderung stagen.",
            (git("add", "README.md"),),
            watch="README.md gleitet in den Staging Bereich.",
        ),
        Step(
            "partial-staging",
            "Staging Bereich",
            "Nach dem `add` noch einmal ändern: Der Staging Bereich hält den alten Stand fest, "
            "die neue Änderung liegt nur im Working Tree.",
            (Write("README.md", "Kapitel 2: Branches", append=True),),
            watch="README.md steht jetzt in beiden Spalten.",
        ),
        Step(
            "unstage",
            "Staging Bereich",
            "`git restore --staged` nimmt die Datei wieder aus dem Staging Bereich.",
            (git("restore", "--staged", "README.md"),),
            watch="README.md gleitet zurück in den Working Tree (nur noch dort).",
        ),
        Step(
            "commit-all",
            "Staging Bereich",
            "Alles stagen und committen.",
            (git("add", "README.md"), git("commit", "-m", "Kapitel ergänzen")),
            watch="README.md fliegt in den neuen Commit.",
        ),
        # --- 4. branch -----------------------------------------------------------
        Step(
            "branch",
            "Branches",
            "Ein Branch ist nur ein Zeiger. `git switch -c` legt ihn an und hängt HEAD daran.",
            (git("switch", "-c", "feature"),),
            watch="Neues Label „feature“ am selben Commit; HEAD gleitet von main zu feature.",
        ),
        Step(
            "feature-commit",
            "Branches",
            "Ein Commit auf feature: nur feature und HEAD rücken weiter, main bleibt stehen.",
            (Write("feature.txt", "Neue Funktion"), git("add", "feature.txt"), git("commit", "-m", "Feature bauen")),
            watch="Neuer Commit; feature + HEAD gleiten mit, main bleibt zurück.",
        ),
        Step(
            "switch-main",
            "Branches",
            "Zurück auf main: HEAD wechselt, feature.txt verschwindet aus dem Ordner.",
            (git("switch", "main"),),
            watch="HEAD gleitet zum Label main.",
        ),
        # --- 5. merges -----------------------------------------------------------
        Step(
            "fast-forward",
            "Merge",
            "main ist Vorfahre von feature: Der Merge schiebt main nur vor (Fast-forward), "
            "es entsteht kein neuer Commit.",
            (git("merge", "feature"),),
            watch="main (mit HEAD) gleitet nach vorn zu feature – kein neuer Commit.",
        ),
        Step(
            "delete-merged-branch",
            "Merge",
            "Der gemergte Branch wird nicht mehr gebraucht.",
            (git("branch", "-d", "feature"),),
            watch="Das Label feature blendet aus; alle Commits bleiben.",
        ),
        Step(
            "diverge",
            "Merge",
            "Zwei Branches entwickeln sich auseinander: ein Commit auf login, einer auf main.",
            (
                git("switch", "-c", "login"),
                Write("login.py", "def login(): ..."),
                git("add", "login.py"),
                git("commit", "-m", "Login"),
                git("switch", "main"),
                Write("hallo.py", "print('Tschüss')", append=True),
                git("commit", "-am", "Abschied"),
            ),
            watch="Die History verzweigt sich; login bekommt eine eigene Spur und Farbe.",
        ),
        Step(
            "three-way-merge",
            "Merge",
            "Jetzt ist kein Fast-forward möglich: git erzeugt einen Merge-Commit mit zwei Eltern.",
            (git("merge", "--no-edit", "login"),),
            watch="Neuer Merge-Commit mit Kanten zu beiden Eltern; main + HEAD gleiten hin.",
        ),
        # --- 6. merge conflict ---------------------------------------------------
        Step(
            "conflict-setup",
            "Merge-Konflikt",
            "Vorbereitung: config.txt wird auf main und auf farbe unterschiedlich geändert.",
            (
                Write("config.txt", "farbe = grün"),
                git("add", "config.txt"),
                git("commit", "-m", "Konfiguration"),
                git("switch", "-c", "farbe"),
                Write("config.txt", "farbe = blau"),
                git("commit", "-am", "Blau"),
                git("switch", "main"),
                Write("config.txt", "farbe = rot"),
                git("commit", "-am", "Rot"),
            ),
            watch="Zwei neue Spitzen: farbe und main, beide mit Änderung an config.txt.",
        ),
        Step(
            "conflict",
            "Merge-Konflikt",
            "Beide Seiten haben dieselbe Zeile geändert – git hält den Merge an.",
            (git("merge", "farbe", fails=True),),
            watch="Rotes Banner „Merge läuft – 1 Konflikt“; config.txt im Working Tree mit rotem "
            "„Konflikt“-Rahmen.",
        ),
        Step(
            "resolve",
            "Merge-Konflikt",
            "Konflikt von Hand lösen und die Datei mit `git add` als gelöst markieren.",
            (Write("config.txt", "farbe = lila"), git("add", "config.txt")),
            watch="config.txt gleitet in den Staging Bereich; Banner wird gelb: "
            "„Merge läuft – keine Konflikte mehr“.",
        ),
        Step(
            "conclude-merge",
            "Merge-Konflikt",
            "Der Commit schließt den Merge ab.",
            (git("commit", "--no-edit"),),
            watch="Merge-Commit wächst ein, das Banner blendet aus.",
        ),
        # --- 7. Ghost Commits ----------------------------------------------------
        Step(
            "typo-commit",
            "Ghost Commits",
            "Ein Commit mit Tippfehler.",
            (Write("notizen.txt", "Tipfehler"), git("add", "notizen.txt"), git("commit", "-m", "Notizen")),
            watch="Neuer Commit „Notizen“.",
        ),
        Step(
            "amend",
            "Ghost Commits",
            "`commit --amend` ändert den Commit nicht, sondern ersetzt ihn durch einen neuen.",
            (Write("notizen.txt", "Tippfehler"), git("commit", "-a", "--amend", "-m", "Notizen (korrigiert)")),
            watch="Der neue Commit wächst ein; der ersetzte bleibt blass als Ghost Commit stehen.",
        ),
        Step(
            "rebase-setup",
            "Ghost Commits",
            "Vorbereitung: Branch experiment mit zwei Commits, danach einer auf main.",
            (
                git("switch", "-c", "experiment"),
                Write("experiment.txt", "Versuch 1"),
                git("add", "experiment.txt"),
                git("commit", "-m", "Versuch 1"),
                Write("experiment.txt", "Versuch 2", append=True),
                git("commit", "-am", "Versuch 2"),
                git("switch", "main"),
                Write("hallo.py", "print('Bis bald')", append=True),
                git("commit", "-am", "Gruß ändern"),
                git("switch", "experiment"),
            ),
            watch="Neue Commits; die Ghost Commits vom amend verschwinden (Refs haben sich bewegt).",
        ),
        Step(
            "rebase",
            "Ghost Commits",
            "`git rebase main` kopiert die zwei Commits auf die Spitze von main. "
            "Die Originale sind danach von keinem Branch mehr erreichbar.",
            (git("rebase", "main"),),
            watch="Zwei Kopien wachsen hinter main ein, experiment + HEAD gleiten hin; "
            "die Originale bleiben blass als Ghost Commits.",
        ),
        Step(
            "clear-ghosts",
            "Ghost Commits",
            "In der Live View `Esc` drücken: Die Ghost Commits werden ausgeblendet. "
            "(Kein git-Befehl – Enter drücken, wenn erledigt.)",
            live_view_key="Esc",
            watch="Die blassen Commits verschwinden.",
        ),
        Step(
            "rebase-conflict-setup",
            "Ghost Commits",
            "Vorbereitung für einen angehaltenen Rebase: main und experiment ändern beide experiment.txt.",
            (
                Write("experiment.txt", "Versuch 3", append=True),
                git("commit", "-am", "Versuch 3"),
                git("switch", "main"),
                Write("experiment.txt", "Endgültig"),
                git("add", "experiment.txt"),
                git("commit", "-m", "Experiment beenden"),
                git("switch", "experiment"),
            ),
            watch="main und experiment laufen wieder auseinander.",
        ),
        Step(
            "rebase-conflict",
            "Ghost Commits",
            "Der Rebase hält beim ersten Commit mit Konflikt an. HEAD zeigt jetzt direkt auf "
            "einen Commit (detached).",
            (git("rebase", "main", fails=True),),
            watch="Banner „Rebase 1/3 – 1 Konflikt“; HEAD sitzt losgelöst an einem Commit; "
            "experiment.txt mit rotem Rahmen.",
        ),
        Step(
            "rebase-abort",
            "Ghost Commits",
            "`git rebase --abort` bricht ab: alles ist wieder wie vorher.",
            (git("rebase", "--abort"),),
            watch="Banner blendet aus, HEAD hängt wieder an experiment.",
        ),
        Step(
            "delete-unmerged-branch",
            "Ghost Commits",
            "`git branch -D` löscht auch einen nicht gemergten Branch – seine Commits werden unerreichbar.",
            (git("switch", "main"), git("branch", "-D", "experiment")),
            watch="Das Label experiment blendet aus, seine Commits werden Ghost Commits.",
        ),
        # --- 8. Remote -----------------------------------------------------------
        Step(
            "remote-create",
            "Remote",
            "Ein leeres Repository ohne Working Tree (bare) als „Server“ anlegen und als Remote origin eintragen.",
            (git("init", "--bare", "-b", "main", f"../{REMOTE}"), git("remote", "add", "origin", f"../{REMOTE}")),
            watch="Rechts erscheint die Remote-Box origin (noch ohne Remote-tracking Branches).",
        ),
        Step(
            "push-upstream",
            "Remote",
            "`git push -u` lädt main hoch und trägt origin/main als Upstream ein.",
            (git("push", "-u", "origin", "main"),),
            watch="Umrandetes Label origin/main in der Farbe von main; main zeigt ↑0 ↓0; "
            "die Box zeigt weiter „noch nie geholt“ (ein Push ist kein Holen).",
        ),
        Step(
            "local-ahead",
            "Remote",
            "Ein lokaler Commit: main ist dem Upstream einen Commit voraus.",
            (Write("hallo.py", "print('Neu')", append=True), git("commit", "-am", "Lokale Änderung")),
            watch="main zeigt ↑1 ↓0; origin/main bleibt stehen.",
        ),
        Step(
            "push",
            "Remote",
            "`git push` überträgt den Commit.",
            (git("push"),),
            watch="origin/main gleitet zu main; ↑0 ↓0.",
        ),
        Step(
            "colleague-pushes",
            "Remote",
            "Eine Kollegin klont den Server, committet und pusht. Die Live View merkt davon nichts – "
            "sie fragt den Server nie selbst.",
            (
                git("clone", f"../{REMOTE}", colleague),
                Write(f"{colleague}/kollegin.txt", "Gruß von der Kollegin"),
                git("-C", colleague, "add", "kollegin.txt"),
                git("-C", colleague, "commit", "-m", "Beitrag der Kollegin"),
                git("-C", colleague, "push"),
            ),
            watch="In der Live View ändert sich nichts.",
        ),
        Step(
            "fetch",
            "Remote",
            "`git fetch` holt den neuen Stand: origin/main rückt vor, main bleibt stehen.",
            (git("fetch"),),
            watch="Der Commit der Kollegin erscheint, origin/main gleitet hin; main zeigt ↑0 ↓1; "
            "„zuletzt geholt gerade eben“.",
        ),
        Step(
            "diverged",
            "Remote",
            "Gleichzeitig ein eigener Commit: main ist jetzt voraus und hinterher.",
            (Write("README.md", "Kapitel 3: Remotes", append=True), git("commit", "-am", "Kapitel 3")),
            watch="main zeigt ↑1 ↓1.",
        ),
        Step(
            "pull",
            "Remote",
            "`git pull` = fetch + merge: der Stand der Kollegin wird eingemergt.",
            (git("pull", "--no-rebase", "--no-edit"),),
            watch="Merge-Commit wächst ein; main zeigt ↑2 ↓0.",
        ),
        Step(
            "push-merged",
            "Remote",
            "Push – lokal und Upstream sind wieder gleich.",
            (git("push"),),
            watch="origin/main gleitet zu main; ↑0 ↓0.",
        ),
        Step(
            "push-without-upstream",
            "Remote",
            "Neuer Branch, gepusht ohne `-u`: origin/neu existiert, ist aber nicht sein Upstream.",
            (git("switch", "-c", "neu"), git("push", "origin", "neu")),
            watch="Label origin/neu erscheint, aber neu zeigt keinen ↑/↓-Zähler.",
        ),
        Step(
            "set-upstream",
            "Remote",
            "Mit `git push -u` wird origin/neu zum Upstream von neu.",
            (git("push", "-u", "origin", "neu"),),
            watch="neu zeigt jetzt ↑0 ↓0; origin/neu hat die Farbe von neu.",
        ),
    )


STEPS: tuple[Step, ...] = _steps()


@dataclass
class DemoFolder:
    """The fresh temporary folder that holds every repository of the demo."""

    root: Path
    _env: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self._env = _isolated_git_env(self.root)

    @property
    def observed(self) -> Path:
        return self.root / OBSERVED

    def inside(self, path: Path) -> Path:
        """``path`` resolved; raises unless it is the demo folder or lies inside it."""
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise OutsideDemoFolderError(f"{resolved} liegt außerhalb des Demo-Ordners {self.root}")
        return resolved

    def run(self, action: Action) -> subprocess.CompletedProcess[str] | None:
        """Run ``action`` in the Observed Repository, checking every path stays inside."""
        cwd = self.inside(self.observed)
        if isinstance(action, Write):
            target = self.inside(cwd / action.path)
            with target.open("a" if action.append else "w", encoding="utf-8") as file:
                file.write(action.line + "\n")
            return None
        for argument in action.args:
            if "/" in argument or argument.startswith("."):
                self.inside(cwd / argument)
        result = subprocess.run(
            ["git", *action.args], cwd=cwd, env=self._env, capture_output=True, text=True
        )
        if (result.returncode != 0) != action.fails:
            expectation = "fehlschlagen" if action.fails else "gelingen"
            raise RuntimeError(
                f"`{action.shown()}` sollte {expectation} (Exit-Code {result.returncode}):\n"
                f"{result.stdout}{result.stderr}"
            )
        return result


def _isolated_git_env(root: Path) -> dict[str, str]:
    """The environment for the demo's git commands.

    Repository-selecting variables are dropped, discovery stops at the demo folder, and
    the lecturer's global/system configuration (signing, ``pull.rebase``, hooks …) is
    ignored so the demo always behaves the same. Editors never open.
    """
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_CEILING_DIRECTORIES=str(root.parent),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Dozent",
        GIT_AUTHOR_EMAIL="dozent@example.org",
        GIT_COMMITTER_NAME="Dozent",
        GIT_COMMITTER_EMAIL="dozent@example.org",
        GIT_EDITOR="true",
        GIT_TERMINAL_PROMPT="0",
    )
    return env


def create_demo_folder() -> DemoFolder:
    """A new, empty temporary folder with the empty (not yet initialised) ``vorlesung``."""
    root = Path(tempfile.mkdtemp(prefix="git-visualizer-demo-"))
    if any(root.iterdir()):
        raise OutsideDemoFolderError(f"{root} ist nicht leer")
    folder = DemoFolder(root)
    folder.observed.mkdir()
    return folder


Prompt = Callable[[str], str]
StepDone = Callable[[Step, DemoFolder], None]


def live_view_command(folder: DemoFolder) -> list[str]:
    return ["git-visualizer", str(folder.observed)]


def run_demo(
    *,
    prompt: Prompt | None = input,
    out: TextIO = sys.stdout,
    launch_live_view: bool = False,
    on_step_done: StepDone | None = None,
    folder: DemoFolder | None = None,
) -> DemoFolder:
    """Run every step; ``prompt=None`` runs them without pausing.

    ``on_step_done`` is called after each step with the folder (tests inspect the
    Live View model there). Typing ``q`` at a prompt ends the demo early.
    """
    folder = folder or create_demo_folder()

    def say(text: str = "") -> None:
        print(text, file=out, flush=True)

    def wait(message: str) -> bool:
        if prompt is None:
            return True
        try:
            return prompt(message).strip().lower() not in {"q", "quit", "exit"}
        except EOFError:
            return False

    say(f"Demo-Ordner (temporär): {folder.root}")
    say("Live View in einem zweiten Terminal starten:")
    say(f"  {shlex.join(live_view_command(folder))}")
    if launch_live_view:
        subprocess.Popen([sys.executable, "-m", "git_visualizer", str(folder.observed)])
        say("(Live View wurde gestartet.)")
    say(f"Alle Befehle laufen in: {folder.observed}")
    if not wait("\nEnter: los geht's (q: beenden) "):
        return _finish(folder, say)

    chapter = ""
    for number, step in enumerate(STEPS, start=1):
        if step.chapter != chapter:
            chapter = step.chapter
            say(f"\n=== {chapter} ===")
        say(f"\n[{number}/{len(STEPS)}] {step.explanation}")
        for action in step.actions:
            say(f"  $ {action.shown()}")
        if step.live_view_key:
            say(f"  ⌨ In der Live View: {step.live_view_key}")
        if not wait("Enter: ausführen (q: beenden) " if step.actions else "Enter: weiter (q: beenden) "):
            return _finish(folder, say)
        for action in step.actions:
            result = folder.run(action)
            if result is not None:
                for line in (result.stdout + result.stderr).strip().splitlines():
                    say(f"    {line}")
        if step.watch:
            say(f"  → Live View: {step.watch}")
        if on_step_done is not None:
            on_step_done(step, folder)

    say("\nFertig.")
    return _finish(folder, say)


def _finish(folder: DemoFolder, say: Callable[[str], None]) -> DemoFolder:
    say(f"Der Demo-Ordner bleibt erhalten: {folder.root}")
    say(f"Aufräumen: rm -rf {shlex.quote(str(folder.root))}")
    return folder


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="git-visualizer-demo",
        description="Führt Schritt für Schritt durch eine git-Vorlesung – in einem neuen "
        "temporären Ordner, nie in einem bestehenden Repository.",
    )
    parser.add_argument("--live-view", action="store_true", help="die Live View auf dem Demo-Repository starten")
    parser.add_argument("--no-pause", action="store_true", help="alle Schritte ohne Warten ausführen")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_demo(prompt=None if args.no_pause else input, launch_live_view=args.live_view)
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
