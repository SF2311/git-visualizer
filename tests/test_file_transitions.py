"""Ticket 06: animated file transitions — files moving between the Working Tree and the
Staging Area, appearing and disappearing, and committed into a new commit."""

from __future__ import annotations

from typing import Any

from conftest import GitRepo
from model_output import prop, rows
from PySide6.QtCore import QAbstractItemModel

from git_visualizer.live_view import LiveViewModel

FILE_KINDS = ("fileMoved", "fileAppeared", "fileDisappeared", "fileCommitted")
WT, SA = "workingTree", "stagingArea"


def _watching(repo: GitRepo) -> LiveViewModel:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    return model


def _file_transitions(model: LiveViewModel) -> list[tuple[str, str, str, str, str]]:
    return [
        (t["kind"], t["path"], t["fromArea"], t["toArea"], t["toHash"])
        for t in rows(model, "transitions")
        if t["kind"] in FILE_KINDS
    ]


def _files(model: LiveViewModel, column: str) -> list[tuple[str, str]]:
    return [(entry["path"], entry["change"]) for entry in rows(model, column)]


def _head(repo: GitRepo) -> str:
    return repo.git("rev-parse", "HEAD").strip()


def test_add_moves_the_file_from_the_working_tree_to_the_staging_area(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    model = _watching(repo)

    repo.git("add", "login.py")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileMoved", "login.py", WT, SA, "")]
    assert [t["kind"] for t in rows(model, "transitions")] == ["fileMoved"]


def test_restore_staged_moves_the_file_back_to_the_working_tree(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")
    repo.git("add", "README.md")
    model = _watching(repo)

    repo.git("restore", "--staged", "README.md")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileMoved", "README.md", SA, WT, "")]
    assert _files(model, "workingTreeFiles") == [("README.md", "modified")]


def test_commit_of_two_staged_files_commits_both_into_the_new_commit(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("a.txt", "a\n")
    repo.write("b.txt", "b\n")
    repo.git("add", "a.txt", "b.txt")
    model = _watching(repo)

    repo.git("commit", "-q", "-m", "Zwei Dateien")
    model.notifyRepositoryChanged()
    new = _head(repo)

    assert _file_transitions(model) == [
        ("fileCommitted", "a.txt", SA, "", new),
        ("fileCommitted", "b.txt", SA, "", new),
    ]
    assert ("commitAdded", new) in [(t["kind"], t["toHash"]) for t in rows(model, "transitions")]
    assert rows(model, "stagingAreaFiles") == []


def test_editing_a_staged_file_makes_it_appear_in_the_working_tree_too(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    repo.git("add", "login.py")
    model = _watching(repo)

    repo.write("login.py", "v2\n")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileAppeared", "login.py", "", WT, "")]
    assert _files(model, "stagingAreaFiles") == [("login.py", "new")]
    assert _files(model, "workingTreeFiles") == [("login.py", "modified")]


def test_new_untracked_file_appears_and_a_deleted_one_disappears(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = _watching(repo)

    repo.write("notizen.txt", "neu\n")
    model.notifyRepositoryChanged()
    assert _file_transitions(model) == [("fileAppeared", "notizen.txt", "", WT, "")]

    (repo.path / "notizen.txt").unlink()
    model.notifyRepositoryChanged()
    assert _file_transitions(model) == [("fileDisappeared", "notizen.txt", WT, "", "")]


def test_adding_a_partially_staged_file_moves_its_working_tree_entry(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    repo.git("add", "login.py")
    repo.write("login.py", "v2\n")
    model = _watching(repo)

    repo.git("add", "login.py")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileMoved", "login.py", WT, SA, "")]


def test_committing_a_partially_staged_file_keeps_its_working_tree_entry(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    repo.git("add", "login.py")
    repo.write("login.py", "v2\n")
    model = _watching(repo)

    repo.git("commit", "-q", "-m", "Login")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileCommitted", "login.py", SA, "", _head(repo))]
    assert _files(model, "workingTreeFiles") == [("login.py", "modified")]


def test_commit_all_commits_files_straight_from_the_working_tree(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")
    model = _watching(repo)

    repo.git("commit", "-q", "-a", "-m", "Alles")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileCommitted", "README.md", WT, "", _head(repo))]


def test_unstaging_without_a_working_tree_copy_makes_the_file_disappear(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")
    repo.git("add", "README.md")
    model = _watching(repo)

    repo.git("restore", "--staged", "--worktree", "README.md")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileDisappeared", "README.md", SA, "", "")]


def test_soft_reset_makes_the_committed_files_appear_in_the_staging_area(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.commit("Zweiter Commit", file="login.py")
    model = _watching(repo)

    repo.git("reset", "-q", "--soft", "HEAD~1")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == [("fileAppeared", "login.py", "", SA, "")]


def test_checking_out_a_ghost_commit_commits_no_files(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    original = repo.commit("Login", file="login.py")
    model = _watching(repo)
    repo.write("login.py", "Login korrigiert\n")
    repo.git("add", "login.py")
    repo.git("commit", "-q", "--amend", "-m", "Login (korrigiert)")
    model.notifyRepositoryChanged()
    assert original in prop(model, "ghostCommitHashes")
    repo.write("login.py", "Login\n")  # the Ghost Commit's content, staged
    repo.git("add", "login.py")
    model.notifyRepositoryChanged()
    assert _files(model, "stagingAreaFiles") == [("login.py", "modified")]

    repo.git("checkout", "-q", "--detach", original)
    model.notifyRepositoryChanged()

    assert _head(repo) == original
    assert _file_transitions(model) == [("fileDisappeared", "login.py", SA, "", "")]


def test_unchanged_files_and_unchanged_refreshes_have_no_file_transitions(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("notizen.txt", "neu\n")
    repo.write("README.md", "geändert\n")
    repo.git("add", "README.md")
    model = _watching(repo)
    assert _file_transitions(model) == []

    repo.write("notizen.txt", "noch neuer\n")
    model.notifyRepositoryChanged()

    assert _file_transitions(model) == []


def test_file_transitions_are_exposed_as_a_list_for_the_view(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("a.txt", "a\n")
    repo.git("add", "a.txt")
    model = _watching(repo)

    repo.git("commit", "-q", "-m", "A")
    model.notifyRepositoryChanged()

    assert prop(model, "fileTransitions") == [
        {"kind": "fileCommitted", "path": "a.txt", "fromArea": SA, "toArea": "", "toHash": _head(repo)}
    ]


def test_history_transitions_have_no_file_roles(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    model = _watching(repo)

    repo.commit("Zweiter Commit")
    model.notifyRepositoryChanged()

    assert {(t["path"], t["fromArea"], t["toArea"]) for t in rows(model, "transitions")} == {("", "", "")}


# --- Keyed file lists: delegates persist across refreshes --------------------------


def _events(list_model: Any) -> list[str]:
    assert isinstance(list_model, QAbstractItemModel)
    events: list[str] = []
    list_model.modelReset.connect(lambda: events.append("reset"))
    list_model.rowsInserted.connect(lambda *_args: events.append("inserted"))
    list_model.rowsRemoved.connect(lambda *_args: events.append("removed"))
    return events


def test_file_lists_update_row_by_row(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("a.txt", "a\n")
    repo.write("b.txt", "b\n")
    model = _watching(repo)
    working_tree = _events(prop(model, "workingTreeFiles"))
    staging_area = _events(prop(model, "stagingAreaFiles"))

    repo.git("add", "a.txt")
    model.notifyRepositoryChanged()

    assert working_tree == ["removed"]
    assert staging_area == ["inserted"]
