"""ADR 0001: neither refreshing the Live View model nor watching modifies the Observed Repository."""

from __future__ import annotations

import os
import time
from pathlib import Path

from conftest import GitRepo
from PySide6.QtGui import QGuiApplication

from git_visualizer.live_view import LiveViewModel
from git_visualizer.watcher import RepositoryWatcher


def _repository_state(path: Path) -> dict[str, tuple[bytes, int]]:
    """Content and mtime of every file in the Working Tree and the git directory."""
    return {
        str(file.relative_to(path)): (file.read_bytes(), file.stat().st_mtime_ns)
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def test_refresh_leaves_refs_index_and_working_tree_untouched(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.commit("Zweiter Commit", file="src/app.py")
    repo.write("untracked.txt", "neu\n")
    repo.write("README.md", "geändert\n")
    # Make the index stat-dirty: a careless `git status` would now rewrite it.
    readme = repo.path / "README.md"
    stat = readme.stat()
    os.utime(readme, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    before = _repository_state(repo.path)

    model = LiveViewModel(repo.path)
    for _ in range(3):
        model.notifyRepositoryChanged()

    assert _repository_state(repo.path) == before
    assert list(repo.path.rglob("*.lock")) == []


def test_reading_status_leaves_the_index_file_byte_identical(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.commit("Zweiter Commit", file="renamed-source.txt")
    repo.git("mv", "renamed-source.txt", "renamed-target.txt")
    repo.write("staged.txt", "v1\n")
    repo.git("add", "staged.txt")
    repo.write("staged.txt", "v2\n")  # partially staged
    repo.write("untracked.txt", "neu\n")
    # Stat-dirty but unchanged: the index's cached stat data no longer matches the
    # file, so a `git status` with optional locks would refresh and rewrite the index.
    unchanged = repo.path / "README.md"
    stat = unchanged.stat()
    os.utime(unchanged, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    index = repo.path / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)

    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    assert (index.read_bytes(), index.stat().st_mtime_ns) == before
    assert not (repo.path / ".git" / "index.lock").exists()
    # Guard the scenario itself: an ordinary `git status` does rewrite this index.
    repo.git("status")
    assert index.read_bytes() != before[0]


def test_watching_leaves_the_repository_untouched(repo: GitRepo, qapp: QGuiApplication) -> None:
    repo.commit("Erster Commit")
    repo.write(".gitignore", "build/\n")
    repo.write("build/out.o", "binär\n")
    repo.write("README.md", "geändert\n")
    before = _repository_state(repo.path)

    model = LiveViewModel(repo.path)
    watcher = RepositoryWatcher(repo.path, model.notifyRepositoryChanged, poll_interval_ms=20)
    deadline = time.monotonic() + 0.3
    while time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    watcher.stop()

    assert _repository_state(repo.path) == before
    assert list(repo.path.rglob("*.lock")) == []
