"""Ticket 01: a linear History in the Live View model."""

from __future__ import annotations

from conftest import GitRepo
from model_output import prop, rows

from git_visualizer.live_view import LiveViewModel


def test_linear_history_shows_one_column_per_commit_left_to_right(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    second = repo.commit("Add login")
    third = repo.commit("Fix typo")

    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    commits = sorted(rows(model, "commits"), key=lambda c: c["column"])
    assert [(c["hash"], c["column"]) for c in commits] == [(first, 0), (second, 1), (third, 2)]


def test_commit_nodes_show_short_hash_and_first_message_line(repo: GitRepo) -> None:
    repo.write("a.txt", "a\n")
    repo.git("add", "a.txt")
    repo.git("commit", "-q", "-m", "Add login\n\nLonger explanation that is not shown.")
    full_hash = repo.git("rev-parse", "HEAD").strip()

    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    [commit] = rows(model, "commits")
    assert commit["subject"] == "Add login"
    assert commit["shortHash"] == full_hash[:7]


def test_branch_label_sits_on_its_commit_and_head_is_attached_to_it(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    tip = repo.commit("Zweiter Commit")

    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    assert rows(model, "branchLabels") == [
        {"name": "main", "commitHash": tip, "column": 1, "hasHead": True}
    ]
    assert prop(model, "headBranch") == "main"
    assert prop(model, "headDetached") is False
    assert prop(model, "headCommitHash") == tip
    assert prop(model, "headColumn") == 1
    assert prop(model, "columnCount") == 2


def test_refresh_picks_up_new_commits(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    assert len(rows(model, "commits")) == 1

    tip = repo.commit("Zweiter Commit")
    model.notifyRepositoryChanged()

    assert [c["column"] for c in rows(model, "commits")] == [1, 0]
    assert rows(model, "branchLabels")[0]["commitHash"] == tip
    assert prop(model, "headColumn") == 1


def test_empty_repository_has_no_commits_and_head_on_unborn_branch(repo: GitRepo) -> None:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()

    assert rows(model, "commits") == []
    assert rows(model, "branchLabels") == []
    assert prop(model, "headBranch") == "main"
    assert prop(model, "headCommitHash") == ""
    assert prop(model, "headColumn") == -1
    assert prop(model, "columnCount") == 0
