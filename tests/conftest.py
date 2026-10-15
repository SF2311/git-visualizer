"""Shared test harness: real git repositories in temporary directories.

Tests drive the Observed Repository with real ``git`` commands and assert only on
what the Live View model exposes (see ``model_output.rows``).
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication  # noqa: E402


class GitRepo:
    """A real git repository in a temporary directory, driven by real git commands."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.path,
            check=True,
            capture_output=True,
            text=True,
            env=_isolated_git_env(),
        )
        return result.stdout

    def write(self, relative_path: str, content: str) -> None:
        file = self.path / relative_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)

    def commit(self, message: str, file: str | None = None) -> str:
        """Change a file, stage it and commit; returns the new commit's full hash."""
        file = file or "README.md"
        target = self.path / file
        previous = target.read_text() if target.exists() else ""
        self.write(file, previous + message + "\n")
        self.git("add", file)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").strip()


def _isolated_git_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Dozent",
        GIT_AUTHOR_EMAIL="dozent@example.org",
        GIT_COMMITTER_NAME="Dozent",
        GIT_COMMITTER_EMAIL="dozent@example.org",
    )
    return env


@pytest.fixture(scope="session")
def qapp() -> Iterator[QGuiApplication]:
    app = QGuiApplication.instance() or QGuiApplication([])
    assert isinstance(app, QGuiApplication)
    yield app


@pytest.fixture
def repo(tmp_path: Path, qapp: QGuiApplication) -> GitRepo:
    """An initialised, empty Observed Repository whose default branch is ``main``."""
    path = tmp_path / "observed"
    path.mkdir()
    repository = GitRepo(path)
    repository.git("init", "-q", "-b", "main")
    return repository
