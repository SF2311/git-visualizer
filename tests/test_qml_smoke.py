"""Headless smoke check: the QML view loads against a real repository without warnings."""

from __future__ import annotations

from collections.abc import Iterator

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
