"""Entry point: ``git-visualizer <repository path>`` opens the Live View."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from git_visualizer.git_reader import NotARepositoryError
from git_visualizer.live_view import LiveViewModel

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
    parser.add_argument("repository", type=Path, help="Pfad zum beobachteten Repository")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("Git Visualizer")

    model = LiveViewModel(args.repository.resolve())
    try:
        model.notifyRepositoryChanged()
    except NotARepositoryError:
        print(f"Kein git-Repository: {args.repository}", file=sys.stderr)
        return 2

    engine = create_engine(model)
    if not engine.rootObjects():
        return 1
    exit_code = app.exec()
    del engine  # destroy the QML scene before the model it binds to
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
