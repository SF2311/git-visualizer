"""Ticket 04: the Three Areas strip (Working Tree and Staging Area columns)."""

from __future__ import annotations

from conftest import GitRepo
from model_output import prop, rows

from git_visualizer.live_view import LiveViewModel


def _refreshed(repo: GitRepo) -> LiveViewModel:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    return model


def _files(model: LiveViewModel, column: str) -> list[tuple[str, str]]:
    return [(entry["path"], entry["change"]) for entry in rows(model, column)]


def test_untracked_file_is_listed_in_the_working_tree_only(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("notes.txt", "neu\n")

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [("notes.txt", "untracked")]
    assert _files(model, "stagingAreaFiles") == []


def test_untracked_files_in_new_directories_are_listed_individually(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("src/a.py", "a\n")
    repo.write("src/b.py", "b\n")

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [
        ("src/a.py", "untracked"),
        ("src/b.py", "untracked"),
    ]


def test_modified_file_is_listed_in_the_working_tree(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [("README.md", "modified")]
    assert _files(model, "stagingAreaFiles") == []


def test_deleted_but_unstaged_file_is_listed_in_the_working_tree(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    (repo.path / "README.md").unlink()

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [("README.md", "deleted")]
    assert _files(model, "stagingAreaFiles") == []


def test_unchanged_files_are_not_listed(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.commit("Zweiter Commit", file="src/app.py")
    repo.write("changed.txt", "neu\n")

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [("changed.txt", "untracked")]
    assert _files(model, "stagingAreaFiles") == []


def test_clean_repository_has_empty_columns(repo: GitRepo) -> None:
    repo.commit("Erster Commit")

    model = _refreshed(repo)

    assert rows(model, "workingTreeFiles") == []
    assert rows(model, "stagingAreaFiles") == []


def test_staged_new_file_is_listed_in_the_staging_area_only(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "print('login')\n")
    repo.git("add", "login.py")

    model = _refreshed(repo)

    assert _files(model, "stagingAreaFiles") == [("login.py", "new")]
    assert _files(model, "workingTreeFiles") == []


def test_staged_files_before_the_first_commit_are_new(repo: GitRepo) -> None:
    repo.write("README.md", "Hallo\n")
    repo.git("add", "README.md")

    model = _refreshed(repo)

    assert _files(model, "stagingAreaFiles") == [("README.md", "new")]
    assert _files(model, "workingTreeFiles") == []


def test_staged_modification_is_listed_in_the_staging_area(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")
    repo.git("add", "README.md")

    model = _refreshed(repo)

    assert _files(model, "stagingAreaFiles") == [("README.md", "modified")]
    assert _files(model, "workingTreeFiles") == []


def test_file_staged_then_edited_again_appears_in_both_columns(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    repo.git("add", "login.py")
    repo.write("login.py", "v2\n")

    model = _refreshed(repo)

    assert _files(model, "stagingAreaFiles") == [("login.py", "new")]
    assert _files(model, "workingTreeFiles") == [("login.py", "modified")]


def test_staged_deletion_is_listed_in_the_staging_area(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("rm", "-q", "README.md")

    model = _refreshed(repo)

    assert _files(model, "stagingAreaFiles") == [("README.md", "deleted")]
    assert _files(model, "workingTreeFiles") == []


def test_staged_rename_shows_new_and_original_path(repo: GitRepo) -> None:
    repo.write("alt.txt", "Ein Text, lang genug für die Erkennung der Umbenennung.\n")
    repo.git("add", "alt.txt")
    repo.git("commit", "-q", "-m", "Erster Commit")
    repo.git("mv", "alt.txt", "neu.txt")

    model = _refreshed(repo)

    assert rows(model, "stagingAreaFiles") == [
        {"path": "neu.txt", "change": "renamed", "originalPath": "alt.txt", "conflicted": False}
    ]
    assert _files(model, "workingTreeFiles") == []


def test_entries_without_rename_have_no_original_path(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("README.md", "geändert\n")

    model = _refreshed(repo)

    assert rows(model, "workingTreeFiles") == [
        {"path": "README.md", "change": "modified", "originalPath": "", "conflicted": False}
    ]


def test_paths_with_spaces_and_umlauts_are_shown_verbatim(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("Übung 1.txt", "neu\n")

    model = _refreshed(repo)

    assert _files(model, "workingTreeFiles") == [("Übung 1.txt", "untracked")]


def test_refresh_picks_up_staging(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.write("login.py", "v1\n")
    model = _refreshed(repo)
    assert _files(model, "workingTreeFiles") == [("login.py", "untracked")]

    repo.git("add", "login.py")
    model.notifyRepositoryChanged()

    assert _files(model, "workingTreeFiles") == []
    assert _files(model, "stagingAreaFiles") == [("login.py", "new")]


def test_head_commit_is_identified_for_highlighting(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    tip = repo.commit("Zweiter Commit")

    model = _refreshed(repo)

    assert prop(model, "headCommitHash") == tip
    heads = [c["hash"] for c in rows(model, "commits") if c["hash"] == prop(model, "headCommitHash")]
    assert heads == [tip]
