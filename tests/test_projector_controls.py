"""Headless check of the keyboard-only projector controls in the QML view.

The controls are QML-only state (spec: the QML view owns zoom, themes and the
shortcut overlay), so these tests load the real ``Main.qml``, press keys on the
window and read the resulting QML properties.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from conftest import GitRepo
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QMessageLogContext,
    QObject,
    Qt,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from git_visualizer.app import create_engine
from git_visualizer.live_view import LiveViewModel


class LoadedView:
    def __init__(self, engine: QQmlApplicationEngine, qapp: QGuiApplication) -> None:
        self.engine = engine
        self.qapp = qapp
        window = engine.rootObjects()[0]
        assert isinstance(window, QQuickWindow)
        self.window = window
        controls = window.findChild(QObject, "projectorControls")
        assert controls is not None, "ProjectorControls not found"
        self.controls = controls

    def press(self, key: Qt.Key, modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
        QTest.keyClick(self.window, key, modifier)
        self.qapp.processEvents()

    def control(self, name: str) -> Any:
        return self.controls.property(name)

    def history(self, name: str) -> Any:
        history = self.window.findChild(QObject, "history")
        assert history is not None
        return history.property(name)

    def background(self) -> str:
        color = self.window.property("color")
        assert isinstance(color, QColor)
        return str(color.name())


@pytest.fixture
def view(repo: GitRepo, qapp: QGuiApplication) -> Iterator[LoadedView]:
    repo.commit("Erster Commit")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    engine = create_engine(model)
    loaded = LoadedView(engine, qapp)
    loaded.window.requestActivate()
    QTest.qWaitForWindowExposed(loaded.window)
    qapp.processEvents()
    yield loaded
    # Destroy the QML scene before the model it binds to.
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    del model


def test_light_theme_is_default_and_t_toggles_dark(view: LoadedView) -> None:
    assert view.control("darkTheme") is False
    light = view.background()

    view.press(Qt.Key.Key_T)
    assert view.control("darkTheme") is True
    assert view.background() != light

    view.press(Qt.Key.Key_T)
    assert view.control("darkTheme") is False
    assert view.background() == light


def test_ctrl_plus_and_ctrl_minus_zoom(view: LoadedView) -> None:
    assert view.control("zoom") == pytest.approx(1.0)

    view.press(Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
    zoomed_in = view.control("zoom")
    assert zoomed_in > 1.0

    view.press(Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    view.press(Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    assert view.control("zoom") < 1.0


def test_zoom_is_bounded(view: LoadedView) -> None:
    for _ in range(50):
        view.press(Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    assert view.control("zoom") > 0.3
    for _ in range(100):
        view.press(Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
    assert view.control("zoom") <= 4.0


def test_question_mark_toggles_shortcut_overlay(view: LoadedView) -> None:
    assert view.control("shortcutOverlayVisible") is False

    # Real keyboards send Shift+?; Qt's xkb key mapper also matches it against "?",
    # but the offscreen platform has no key mapper, so the test presses plain "?".
    view.press(Qt.Key.Key_Question)
    assert view.control("shortcutOverlayVisible") is True

    view.press(Qt.Key.Key_Question)
    assert view.control("shortcutOverlayVisible") is False


def test_shortcut_overlay_lists_the_shortcuts_in_german(view: LoadedView) -> None:
    listed = view.control("shortcuts").toVariant()
    keys = [entry["keys"] for entry in listed]
    assert {"Strg +", "Strg −", "T", "?"} <= set(keys)
    descriptions = " ".join(entry["description"] for entry in listed)
    assert "Vergrößern" in descriptions
    assert "Tastenkürzel" in descriptions


def test_history_shrinks_to_fit_a_window_too_narrow_for_it(
    repo: GitRepo, view: LoadedView
) -> None:
    assert view.history("fitScale") == pytest.approx(1.0)

    view.window.setWidth(500)
    view.qapp.processEvents()
    for index in range(2, 5):
        repo.commit(f"Commit {index}")
    view.window.property("liveView").notifyRepositoryChanged()
    view.qapp.processEvents()

    assert view.history("fitScale") < 1.0


def test_every_control_works_without_qml_warnings(view: LoadedView) -> None:
    messages: list[str] = []

    def handler(kind: QtMsgType, context: QMessageLogContext, message: str) -> None:
        if kind != QtMsgType.QtDebugMsg:
            messages.append(message)

    previous = qInstallMessageHandler(handler)
    try:
        view.press(Qt.Key.Key_T)
        view.press(Qt.Key.Key_Question)
        view.press(Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
        view.press(Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
        view.window.grabWindow()
    finally:
        qInstallMessageHandler(previous)

    assert view.control("zoom") == pytest.approx(1.0)
    assert messages == []


def test_auto_fit_does_not_undo_zooming_in(repo: GitRepo, view: LoadedView) -> None:
    for index in range(2, 12):
        repo.commit(f"Commit {index}")
    view.window.property("liveView").notifyRepositoryChanged()
    view.qapp.processEvents()
    before = view.history("fitScale") * view.control("zoom")

    view.press(Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)

    assert view.history("fitScale") * view.control("zoom") > before


def test_escape_clears_ghost_commits_and_is_listed(repo: GitRepo, view: LoadedView) -> None:
    live_view = view.window.property("liveView")
    repo.git("commit", "-q", "--amend", "-m", "Erster Commit, korrigiert")
    live_view.notifyRepositoryChanged()
    view.qapp.processEvents()
    assert len(live_view.property("ghostCommitHashes")) == 1

    view.press(Qt.Key.Key_Escape)

    assert live_view.property("ghostCommitHashes") == []
    listed = view.control("shortcuts").toVariant()
    assert "Esc" in [entry["keys"] for entry in listed]


def test_l_toggles_the_legend_and_is_listed(view: LoadedView) -> None:
    assert view.control("legendVisible") is False
    legend = view.window.findChild(QObject, "legend")
    assert legend is not None, "Legend not found"
    assert legend.property("visible") is False

    view.press(Qt.Key.Key_L)
    assert view.control("legendVisible") is True
    assert legend.property("visible") is True

    view.press(Qt.Key.Key_L)
    assert view.control("legendVisible") is False
    assert legend.property("visible") is False

    listed = view.control("shortcuts").toVariant()
    entry = next(entry for entry in listed if entry["keys"] == "L")
    assert "Legende" in entry["description"]
