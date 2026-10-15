# Git Visualizer

A read-only, projector-friendly Live View of a real git repository that the lecturer
manipulates in a separate terminal. See `CONTEXT.md` for the vocabulary and
`docs/adr/` for the key decisions.

## Install and run

```sh
uv tool install .        # or: pipx install .
git-visualizer /path/to/repository
```

`F5` re-reads the repository (temporary until the filesystem watcher exists).

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest          # runs headless (QT_QPA_PLATFORM=offscreen is set by the tests)
.venv/bin/mypy            # strict type check of src/ and tests/
```

Layout (`src/git_visualizer/`):

- `git_reader.py` — runs read-only git commands and produces an immutable Repository Snapshot (`snapshot.py`)
- `history_layout.py` — columns by ancestry
- `live_view/` — `LiveViewModel`, the single object QML binds to and the single test seam
- `qml/` — the view (`Main.qml`, `HistoryView.qml`, components, `Theme` singleton)
- `app.py` — console entry point

Tests create real repositories in temporary directories, drive them with real `git`
commands and assert only on what the Live View model exposes (`tests/model_output.py`).
