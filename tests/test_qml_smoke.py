"""Headless smoke check: the QML view loads against a real repository without warnings."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import GitRepo
from PySide6.QtCore import QtMsgType, QMessageLogContext, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication

from git_visualizer.app import create_engine
from git_visualizer.live_view import LiveViewModel


@pytest.fixture
def qt_messages() -> Iterator[list[str]]:
    messages: list[str] = []

    def handler(kind: QtMsgType, context: QMessageLogContext, message: str) -> None:
        if kind != QtMsgType.QtDebugMsg:
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    yield messages
    qInstallMessageHandler(previous)


def test_qml_view_loads_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    repo.commit("Erster Commit")
    repo.commit("Add login")
    repo.write("login.py", "v1\n")
    repo.git("add", "login.py")
    repo.write("login.py", "v2\n")  # Working Tree and Staging Area both populated
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    engine = create_engine(model)
    qapp.processEvents()

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()


def test_qml_view_loads_a_branching_history_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    for i in range(4):
        repo.commit(f"Alt {i}")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("tag", "v1.0")
    repo.git("switch", "-q", "main")
    repo.commit("Hauptlinie")
    repo.git("merge", "-q", "--no-edit", "feature")
    repo.git("checkout", "-q", "--detach", "feature")
    model = LiveViewModel(repo.path, max_commits=4)
    model.notifyRepositoryChanged()

    engine = create_engine(model)
    qapp.processEvents()

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()


def test_qml_view_loads_without_warnings_in_a_non_repository_folder(
    tmp_path: Path, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    model = LiveViewModel(tmp_path)
    model.notifyRepositoryChanged()

    engine = create_engine(model)
    qapp.processEvents()

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()


def test_qml_view_loads_remotes_and_upstream_without_warnings(
    repo: GitRepo, tmp_path: Path, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    remote = tmp_path / "remote.git"
    GitRepo(tmp_path).git("init", "-q", "--bare", "-b", "main", str(remote))
    repo.commit("Erster Commit")
    repo.git("remote", "add", "origin", str(remote))
    repo.git("push", "-q", "-u", "origin", "main")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("push", "-q", "origin", "feature")  # no Upstream
    repo.git("switch", "-q", "main")
    repo.commit("Lokal")
    repo.git("fetch", "-q")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    engine = create_engine(model)
    qapp.processEvents()

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()
