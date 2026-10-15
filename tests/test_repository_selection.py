"""Ticket 02: a folder that is not (yet) a git repository, and `git init` in it."""

from __future__ import annotations

from pathlib import Path

from conftest import GitRepo
from model_output import prop, rows
from PySide6.QtGui import QGuiApplication

from git_visualizer.live_view import LiveViewModel


def test_non_repository_folder_yields_the_not_a_repository_state(
    tmp_path: Path, qapp: QGuiApplication
) -> None:
    model = LiveViewModel(tmp_path)
    model.notifyRepositoryChanged()

    assert prop(model, "isRepository") is False
    assert rows(model, "commits") == []
    assert rows(model, "branchLabels") == []
    assert prop(model, "headColumn") == -1


def test_git_init_switches_to_an_empty_repository(tmp_path: Path, qapp: QGuiApplication) -> None:
    model = LiveViewModel(tmp_path)
    model.notifyRepositoryChanged()

    GitRepo(tmp_path).git("init", "-q", "-b", "main")
    model.notifyRepositoryChanged()

    assert prop(model, "isRepository") is True
    assert rows(model, "commits") == []
    assert prop(model, "headBranch") == "main"


def test_repository_view_falls_back_to_waiting_when_git_directory_disappears(
    repo: GitRepo,
) -> None:
    repo.commit("Erster Commit")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    assert prop(model, "isRepository") is True

    repo.git("rev-parse", "--git-dir")  # sanity: still a repository
    for child in sorted((repo.path / ".git").rglob("*"), reverse=True):
        child.unlink() if child.is_file() else child.rmdir()
    (repo.path / ".git").rmdir()
    model.notifyRepositoryChanged()

    assert prop(model, "isRepository") is False
    assert rows(model, "commits") == []


def test_model_exposes_the_observed_folder(tmp_path: Path, qapp: QGuiApplication) -> None:
    model = LiveViewModel(tmp_path)
    assert prop(model, "repositoryPath") == str(tmp_path)
