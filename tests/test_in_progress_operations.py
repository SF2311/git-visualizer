"""Ticket 08: In-progress Operations (paused merge, rebase, …) and conflicts."""

from __future__ import annotations

import shutil
import subprocess

import pytest
from conftest import GitRepo
from model_output import prop, rows

from git_visualizer.live_view import LiveViewModel


def _refreshed(repo: GitRepo) -> LiveViewModel:
    model = LiveViewModel(repo.path)
    model.notifyRepositoryChanged()
    return model


def _files(model: LiveViewModel, column: str) -> list[tuple[str, str, bool]]:
    return [(entry["path"], entry["change"], entry["conflicted"]) for entry in rows(model, column)]


def _operation(model: LiveViewModel) -> dict[str, object]:
    return {
        name: prop(model, name)
        for name in ("operationKind", "operationStep", "operationTotal", "conflictCount", "operationBanner")
    }


def _fails(repo: GitRepo, *args: str) -> None:
    """Run a git command that is expected to stop on a conflict (non-zero exit)."""
    with pytest.raises(subprocess.CalledProcessError):
        repo.git(*args)


def _diverged_branches(repo: GitRepo, *files: str) -> None:
    """``main`` and ``feature`` both change each of ``files`` differently."""
    for file in files:
        repo.write(file, "Basis\n")
    repo.git("add", *files)
    repo.git("commit", "-q", "-m", "Basis")
    repo.git("switch", "-q", "-c", "feature")
    for file in files:
        repo.write(file, "Feature\n")
    repo.git("commit", "-q", "-am", "Feature ändert")
    repo.git("switch", "-q", "main")
    for file in files:
        repo.write(file, "Main\n")
    repo.git("commit", "-q", "-am", "Main ändert")


NO_OPERATION = {
    "operationKind": "",
    "operationStep": 0,
    "operationTotal": 0,
    "conflictCount": 0,
    "operationBanner": "",
}


def test_clean_repository_has_no_in_progress_operation(repo: GitRepo) -> None:
    repo.commit("Erster Commit")

    assert _operation(_refreshed(repo)) == NO_OPERATION


def test_merge_with_conflicts_shows_banner_count_and_flagged_files(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt", "b.txt")
    _fails(repo, "merge", "-q", "feature")

    model = _refreshed(repo)

    assert _operation(model) == {
        "operationKind": "merge",
        "operationStep": 0,
        "operationTotal": 0,
        "conflictCount": 2,
        "operationBanner": "Merge läuft – 2 Konflikte",
    }
    assert _files(model, "workingTreeFiles") == [
        ("a.txt", "modified", True),
        ("b.txt", "modified", True),
    ]
    assert _files(model, "stagingAreaFiles") == []


def test_single_conflict_uses_the_singular(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "merge", "-q", "feature")

    assert prop(_refreshed(repo), "operationBanner") == "Merge läuft – 1 Konflikt"


def test_resolving_and_adding_moves_the_file_to_the_staging_area(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt", "b.txt")
    _fails(repo, "merge", "-q", "feature")
    model = _refreshed(repo)

    repo.write("a.txt", "Gelöst\n")
    repo.git("add", "a.txt")
    model.notifyRepositoryChanged()

    assert prop(model, "conflictCount") == 1
    assert prop(model, "operationBanner") == "Merge läuft – 1 Konflikt"
    assert _files(model, "workingTreeFiles") == [("b.txt", "modified", True)]
    assert _files(model, "stagingAreaFiles") == [("a.txt", "modified", False)]

    repo.write("b.txt", "Gelöst\n")
    repo.git("add", "b.txt")
    model.notifyRepositoryChanged()

    assert prop(model, "operationKind") == "merge"
    assert prop(model, "conflictCount") == 0
    assert prop(model, "operationBanner") == "Merge läuft – keine Konflikte mehr"
    assert _files(model, "workingTreeFiles") == []


def test_merge_continue_ends_the_operation(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "merge", "-q", "feature")
    model = _refreshed(repo)
    repo.write("a.txt", "Gelöst\n")
    repo.git("add", "a.txt")

    repo.git("-c", "core.editor=true", "merge", "--continue")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION
    assert rows(model, "commits")[0]["isMerge"] is True


def test_committing_the_merge_ends_the_operation(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "merge", "-q", "feature")
    model = _refreshed(repo)
    repo.write("a.txt", "Gelöst\n")
    repo.git("add", "a.txt")

    repo.git("commit", "-q", "--no-edit")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION


def test_merge_abort_ends_the_operation(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "merge", "-q", "feature")
    model = _refreshed(repo)
    assert prop(model, "operationKind") == "merge"

    repo.git("merge", "--abort")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION
    assert rows(model, "workingTreeFiles") == []


def test_merge_without_commit_is_shown_without_conflicts(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Main", file="main.txt")
    repo.git("merge", "-q", "--no-commit", "feature")

    model = _refreshed(repo)

    assert prop(model, "operationKind") == "merge"
    assert prop(model, "operationBanner") == "Merge läuft – keine Konflikte mehr"


def _rebase_setup(repo: GitRepo) -> None:
    """``feature`` has five commits on top of ``Basis``; the second conflicts with ``main``."""
    repo.write("shared.txt", "Basis\n")
    repo.git("add", "shared.txt")
    repo.git("commit", "-q", "-m", "Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature 1", file="f1.txt")
    repo.write("shared.txt", "Feature\n")
    repo.git("commit", "-q", "-am", "Feature 2")
    repo.commit("Feature 3", file="f3.txt")
    repo.commit("Feature 4", file="f4.txt")
    repo.commit("Feature 5", file="f5.txt")
    repo.git("switch", "-q", "main")
    repo.write("shared.txt", "Main\n")
    repo.git("commit", "-q", "-am", "Main ändert")
    repo.git("switch", "-q", "feature")


def test_rebase_paused_on_conflict_shows_progress_and_detached_head(repo: GitRepo) -> None:
    _rebase_setup(repo)
    _fails(repo, "rebase", "main")

    model = _refreshed(repo)

    assert _operation(model) == {
        "operationKind": "rebase",
        "operationStep": 2,
        "operationTotal": 5,
        "conflictCount": 1,
        "operationBanner": "Rebase 2/5 – 1 Konflikt",
    }
    assert prop(model, "headDetached") is True
    assert prop(model, "headBranch") == ""
    assert _files(model, "workingTreeFiles") == [("shared.txt", "modified", True)]


def test_rebase_continue_finishes_and_reattaches_head(repo: GitRepo) -> None:
    _rebase_setup(repo)
    _fails(repo, "rebase", "main")
    model = _refreshed(repo)
    repo.write("shared.txt", "Gelöst\n")
    repo.git("add", "shared.txt")
    model.notifyRepositoryChanged()
    assert prop(model, "operationBanner") == "Rebase 2/5"

    repo.git("-c", "core.editor=true", "rebase", "--continue")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION
    assert prop(model, "headDetached") is False
    assert prop(model, "headBranch") == "feature"


def test_rebase_abort_ends_the_operation(repo: GitRepo) -> None:
    _rebase_setup(repo)
    _fails(repo, "rebase", "main")
    model = _refreshed(repo)

    repo.git("rebase", "--abort")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION
    assert prop(model, "headBranch") == "feature"


def test_rebase_with_the_apply_backend_shows_progress(repo: GitRepo) -> None:
    _rebase_setup(repo)
    _fails(repo, "rebase", "--apply", "main")

    model = _refreshed(repo)

    assert prop(model, "operationKind") == "rebase"
    assert (prop(model, "operationStep"), prop(model, "operationTotal")) == (2, 5)
    assert prop(model, "operationBanner") == "Rebase 2/5 – 1 Konflikt"


def test_interactive_rebase_paused_on_edit_shows_progress(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.commit("Zwei", file="zwei.txt")
    repo.commit("Drei", file="drei.txt")
    editor = "sed -i -e '1s/^pick/edit/'"

    repo.git("-c", f"sequence.editor={editor}", "rebase", "-q", "-i", "HEAD~2")

    model = _refreshed(repo)
    assert prop(model, "operationBanner") == "Rebase 1/2"
    assert prop(model, "headDetached") is True


def test_cherry_pick_with_conflict_is_shown(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "cherry-pick", "feature")

    model = _refreshed(repo)

    assert prop(model, "operationKind") == "cherry-pick"
    assert prop(model, "operationBanner") == "Cherry-pick läuft – 1 Konflikt"

    repo.git("cherry-pick", "--abort")
    model.notifyRepositoryChanged()
    assert _operation(model) == NO_OPERATION


def test_revert_with_conflict_is_shown(repo: GitRepo) -> None:
    repo.commit("Basis", file="a.txt")
    repo.commit("Zwei", file="a.txt")
    repo.commit("Drei", file="a.txt")
    _fails(repo, "revert", "--no-edit", "HEAD~1")

    model = _refreshed(repo)

    assert prop(model, "operationKind") == "revert"
    assert prop(model, "operationBanner") == "Revert läuft – 1 Konflikt"


def test_banner_disappears_when_the_folder_stops_being_a_repository(repo: GitRepo) -> None:
    _diverged_branches(repo, "a.txt")
    _fails(repo, "merge", "-q", "feature")
    model = _refreshed(repo)
    assert prop(model, "operationBanner") != ""

    shutil.rmtree(repo.path / ".git")
    model.notifyRepositoryChanged()

    assert _operation(model) == NO_OPERATION
