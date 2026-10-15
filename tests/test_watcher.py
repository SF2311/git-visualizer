"""Ticket 02: the watcher turns a burst of changes on disk into one "repository changed"."""

from __future__ import annotations

import time

from conftest import GitRepo
from PySide6.QtGui import QGuiApplication

from git_visualizer.watcher import RepositoryWatcher


def _process_events_for(qapp: QGuiApplication, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)


def test_burst_of_changes_on_disk_leads_to_one_repository_changed_call(
    repo: GitRepo, qapp: QGuiApplication
) -> None:
    repo.commit("Erster Commit")
    calls: list[float] = []
    watcher = RepositoryWatcher(
        repo.path, lambda: calls.append(time.monotonic()), debounce_ms=150, poll_interval_ms=60_000
    )
    _process_events_for(qapp, 0.3)
    assert calls == []

    started = time.monotonic()
    repo.write("neu.txt", "neu\n")
    repo.git("add", "neu.txt")
    repo.git("commit", "-q", "-m", "Zweiter Commit")
    _process_events_for(qapp, 1.0)

    assert len(calls) == 1
    assert calls[0] - started >= 0.15
    watcher.stop()
