"""Headless smoke check: the QML view loads against a real repository without warnings."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from conftest import GitRepo
from PySide6.QtCore import QtMsgType, QMessageLogContext, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

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


def test_qml_view_animates_history_transitions_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    engine = create_engine(model)
    qapp.processEvents()

    steps: list[Callable[[], object]] = [
        lambda: repo.commit("Erster Commit"),
        lambda: repo.git("switch", "-q", "-c", "feature"),
        lambda: repo.commit("Feature", file="feature.txt"),
        lambda: repo.git("tag", "v1"),
        lambda: repo.git("switch", "-q", "main"),
        lambda: repo.git("merge", "-q", "--ff-only", "feature"),
        lambda: repo.git("branch", "-q", "-d", "feature"),
        lambda: repo.git("tag", "-d", "v1"),
        lambda: repo.git("checkout", "-q", "--detach", "HEAD~1"),
    ]
    for step in steps:
        step()
        model.notifyRepositoryChanged()
        QTest.qWait(120)

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()


def test_qml_view_loads_a_paused_merge_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    repo.commit("Basis", file="a.txt")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="a.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Main", file="a.txt")
    with pytest.raises(subprocess.CalledProcessError):
        repo.git("merge", "feature")
    model = LiveViewModel(repo.path)
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


def test_qml_view_shows_and_clears_ghost_commits_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature 1", file="feature.txt")
    repo.commit("Feature 2", file="feature.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Hauptlinie")
    repo.git("switch", "-q", "feature")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    engine = create_engine(model)
    qapp.processEvents()

    steps: list[Callable[[], object]] = [
        lambda: repo.git("rebase", "-q", "main"),
        lambda: repo.git("commit", "-q", "--amend", "-m", "Feature 2, korrigiert"),
        model.clearGhostCommits,
        lambda: repo.git("switch", "-q", "main"),
        lambda: repo.git("branch", "-q", "-D", "feature"),
        lambda: repo.commit("Weiter"),
    ]
    for step in steps:
        step()
        model.notifyRepositoryChanged()
        QTest.qWait(120)

    assert engine.rootObjects(), "Main.qml did not load"

    assert engine.rootObjects(), "Main.qml did not load"
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()


def _flights(engine: Any) -> list[Any]:
    [window] = engine.rootObjects()
    layer = window.findChild(QQuickItem, "fileFlights")
    assert isinstance(layer, QQuickItem)
    return [child for child in layer.childItems() if child.property("path")]


def test_qml_view_animates_file_transitions_without_warnings(
    repo: GitRepo, qapp: QGuiApplication, qt_messages: list[str]
) -> None:
    repo.commit("Erster Commit")
    repo.write("a.txt", "a\n")
    repo.write("b.txt", "b\n")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    engine = create_engine(model)
    QTest.qWait(50)

    repo.git("add", "a.txt", "b.txt")
    model.notifyRepositoryChanged()
    QTest.qWait(50)
    assert sorted(flight.property("path") for flight in _flights(engine)) == ["a.txt", "b.txt"]

    steps: list[Callable[[], object]] = [
        lambda: repo.write("a.txt", "a2\n"),
        lambda: repo.git("restore", "--staged", "b.txt"),
        lambda: repo.git("add", "a.txt"),
        lambda: repo.git("commit", "-q", "-m", "A"),
        lambda: repo.write("README.md", "neu\n"),
        lambda: repo.git("commit", "-q", "-a", "-m", "Alles"),
    ]
    for step in steps:
        step()
        model.notifyRepositoryChanged()
        QTest.qWait(120)
    QTest.qWait(2000)  # longer than the slowest flight (Motion.commitGrowthDelay)

    assert _flights(engine) == []
    assert qt_messages == []
    for root in engine.rootObjects():
        root.deleteLater()
    qapp.processEvents()
