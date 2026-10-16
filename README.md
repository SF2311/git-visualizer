# Git Visualizer

A read-only, projector-friendly Live View of a real git repository that the lecturer
manipulates in a separate terminal. See `CONTEXT.md` for the vocabulary and
`docs/adr/` for the key decisions.

## Install and run

```sh
uv tool install .        # or: pipx install .
git-visualizer /path/to/repository   # or without a path: folder picker
```

The Live View updates on its own after every git command (filesystem watcher with a
~150 ms debounce, plus a 2 s polling fallback). A folder that is not yet a repository
shows "Kein Repository – warte auf `git init`" until `git init` is run in it. `F5`
re-reads the repository manually (hidden fallback).

`--max-commits N` limits the History to the N most recent commits (default 30);
older history is collapsed into "…".

The Live View never fetches: Remote-tracking Branches and "zuletzt geholt" in the
Remote boxes change only after the lecturer runs `fetch`, `pull` or `push`.

## Lecture demo and smoke checklist

```sh
git-visualizer-demo --live-view   # or without --live-view: start the printed git-visualizer command yourself
```

`git-visualizer-demo` walks a fresh repository through a typical lecture (init, commits,
staging, branches, fast-forward and three-way merge, merge conflict, Ghost Commits after
amend/rebase/`branch -D`, a paused rebase, a bare Remote with fetch/push, a colleague's
push and ahead/behind). It creates everything in a new temporary folder and refuses to
touch anything outside it. Each step prints a German explanation and the git commands,
then waits for Enter (`q` quits; `--no-pause` runs straight through). It uses its own
git identity and ignores your global git configuration.

Before a lecture (or after changing the QML), run the demo against the Live View and
work through [`docs/smoke-checklist.md`](docs/smoke-checklist.md): it covers every
animation, both themes, zoom/auto-fit, the legend and the shortcut overlay.

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest          # runs headless (QT_QPA_PLATFORM=offscreen is set by the tests)
.venv/bin/mypy            # strict type check of src/ and tests/
```

Layout (`src/git_visualizer/`):

- `git_cli.py` — `GitCli`, the lock-free runner for read-only git commands
- `git_reader.py` — reads the repository through `GitCli` and produces an immutable Repository Snapshot (`snapshot.py`)
- `remote_reader.py` — Remotes, Remote-tracking Branches and last-fetch times from local metadata (never contacts a Remote)
- `history_layout.py` — columns by ancestry, lanes per branch, label stacking
- `watcher.py` — watches the git directory and the Working Tree, debounces, polls, calls "repository changed"
- `live_view/` — `LiveViewModel`, the single object QML binds to and the single test seam
- `qml/` — the view (`Main.qml`, `HistoryView.qml`, components, `Theme` singleton)
- `app.py` — console entry point
- `lecture_demo.py` — `git-visualizer-demo`, the step-by-step lecture demo

Tests create real repositories in temporary directories, drive them with real `git`
commands and assert only on what the Live View model exposes (`tests/model_output.py`).
