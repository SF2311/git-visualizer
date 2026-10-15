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

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest          # runs headless (QT_QPA_PLATFORM=offscreen is set by the tests)
.venv/bin/mypy            # strict type check of src/ and tests/
```

Layout (`src/git_visualizer/`):

- `git_reader.py` — runs read-only git commands and produces an immutable Repository Snapshot (`snapshot.py`)
- `remote_reader.py` — Remotes, Remote-tracking Branches and last-fetch times from local metadata (never contacts a Remote)
- `history_layout.py` — columns by ancestry, lanes per branch, label stacking
- `watcher.py` — watches the git directory and the Working Tree, debounces, polls, calls "repository changed"
- `live_view/` — `LiveViewModel`, the single object QML binds to and the single test seam
- `qml/` — the view (`Main.qml`, `HistoryView.qml`, components, `Theme` singleton)
- `app.py` — console entry point

Tests create real repositories in temporary directories, drive them with real `git`
commands and assert only on what the Live View model exposes (`tests/model_output.py`).
