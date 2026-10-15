"""Entry point: ``git-visualizer [repository path]`` opens the Live View.

Without a path a folder picker asks for the folder to observe. A folder that is not
(yet) a git repository shows the waiting state until ``git init`` is run in it.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QFileDialog

from git_visualizer.live_view import LiveViewModel
from git_visualizer.watcher import RepositoryWatcher

QML_DIR = Path(__file__).parent / "qml"


def create_engine(model: LiveViewModel) -> QQmlApplicationEngine:
    """Load ``Main.qml`` with ``model`` as its ``liveView``; the engine owns the window."""
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"liveView": model})
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-visualizer",
        description="Live View eines git-Repositorys für die Vorlesung.",
    )
    parser.add_argument(
        "repository",
        type=Path,
        nargs="?",
        help="Pfad zum beobachteten Repository (ohne Angabe: Ordnerauswahl)",
    )
    return parser.parse_args(argv)


def _choose_folder() -> Path | None:
    folder = QFileDialog.getExistingDirectory(
        None, "Ordner für die Live View wählen", str(Path.cwd())
    )
    return Path(folder) if folder else None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    # QApplication (not just QGuiApplication) so that the folder picker can be shown.
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Git Visualizer")

    folder: Path | None = args.repository or _choose_folder()
    if folder is None:
        return 0
    if not folder.is_dir():
        print(f"Kein Ordner: {folder}", file=sys.stderr)
        return 2
    folder = folder.resolve()

    model = LiveViewModel(folder)
    model.notifyRepositoryChanged()
    watcher = RepositoryWatcher(folder, model.notifyRepositoryChanged)

    engine = create_engine(model)
    if not engine.rootObjects():
        return 1
    exit_code = app.exec()
    watcher.stop()
    del engine  # destroy the QML scene before the model it binds to
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
