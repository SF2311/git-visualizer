"""Ticket 07: Ghost Commits — commits that were reachable from a shown ref or HEAD
before a state change and are not afterwards stay in the History, faded, until the
next transition that moves a ref or until they are cleared explicitly."""

from __future__ import annotations

from typing import Any

from conftest import GitRepo
from model_output import prop, rows

from git_visualizer.live_view import LiveViewModel


def _watching(repo: GitRepo, **options: Any) -> LiveViewModel:
    model = LiveViewModel(repo.path, **options)
    model.notifyRepositoryChanged()
    return model


def _commit_rows(model: LiveViewModel) -> dict[str, dict[str, Any]]:
    return {row["hash"]: row for row in rows(model, "commits")}


def _ghosts(model: LiveViewModel) -> set[str]:
    return {row["hash"] for row in rows(model, "commits") if row["isGhost"]}


def _ghost_edges(model: LiveViewModel) -> set[tuple[str, str]]:
    return {(row["childHash"], row["parentHash"]) for row in rows(model, "edges") if row["isGhost"]}


def _head(repo: GitRepo) -> str:
    return repo.git("rev-parse", "HEAD").strip()


def _two_commit_feature_branch(repo: GitRepo) -> tuple[str, str, str]:
    """main: base ← main-only; feature: base ← f1 ← f2 (checked out). Returns base, f1, f2."""
    base = repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    f1 = repo.commit("Feature 1", file="feature.txt")
    f2 = repo.commit("Feature 2", file="feature.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Hauptlinie")
    repo.git("switch", "-q", "feature")
    return base, f1, f2


def test_rebase_leaves_the_original_commits_as_ghost_commits(repo: GitRepo) -> None:
    base, f1, f2 = _two_commit_feature_branch(repo)
    model = _watching(repo)

    repo.git("rebase", "-q", "main")
    model.notifyRepositoryChanged()

    commits = _commit_rows(model)
    copies = {commit_hash for commit_hash, row in commits.items() if row["subject"].startswith("Feature")} - {f1, f2}
    assert len(copies) == 2
    assert _ghosts(model) == {f1, f2}
    assert set(prop(model, "ghostCommitHashes")) == {f1, f2}
    assert not any(commits[copy]["isGhost"] for copy in copies)
    # The originals keep their edges: f2 → f1 → base.
    assert _ghost_edges(model) == {(f2, f1), (f1, base)}


def test_ghost_commits_keep_their_column_and_color(repo: GitRepo) -> None:
    base, f1, f2 = _two_commit_feature_branch(repo)
    model = _watching(repo)
    before = _commit_rows(model)

    repo.git("rebase", "-q", "main")
    model.notifyRepositoryChanged()

    after = _commit_rows(model)
    for ghost in (f1, f2):
        assert after[ghost]["column"] == before[ghost]["column"]
        assert after[ghost]["colorIndex"] == before[ghost]["colorIndex"]
    # The ghost chain does not sit on top of a shown commit.
    occupied = {(row["column"], row["lane"]) for row in after.values() if not row["isGhost"]}
    assert not any((after[ghost]["column"], after[ghost]["lane"]) in occupied for ghost in (f1, f2))


def test_commit_amend_leaves_the_replaced_commit_as_a_ghost_commit(repo: GitRepo) -> None:
    first = repo.commit("Erster Commit")
    replaced = repo.commit("Tippfeler")
    model = _watching(repo)

    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")
    model.notifyRepositoryChanged()

    amended = _head(repo)
    commits = _commit_rows(model)
    assert _ghosts(model) == {replaced}
    assert not commits[amended]["isGhost"]
    assert commits[replaced]["column"] == commits[amended]["column"]
    assert commits[replaced]["lane"] != commits[amended]["lane"]
    assert _ghost_edges(model) == {(replaced, first)}


def test_deleting_an_unmerged_branch_leaves_its_commits_as_ghost_commits(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "experiment")
    e1 = repo.commit("Versuch 1", file="experiment.txt")
    e2 = repo.commit("Versuch 2", file="experiment.txt")
    repo.git("switch", "-q", "main")
    repo.commit("Hauptlinie")
    model = _watching(repo)
    before = _commit_rows(model)

    repo.git("branch", "-q", "-D", "experiment")
    model.notifyRepositoryChanged()

    after = _commit_rows(model)
    assert _ghosts(model) == {e1, e2}
    for ghost in (e1, e2):
        assert (after[ghost]["column"], after[ghost]["lane"], after[ghost]["colorIndex"]) == (
            before[ghost]["column"],
            before[ghost]["lane"],
            before[ghost]["colorIndex"],
        )


def test_deleting_a_merged_branch_leaves_no_ghost_commits(repo: GitRepo) -> None:
    repo.commit("Basis")
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("switch", "-q", "main")
    repo.git("merge", "-q", "--ff-only", "feature")
    model = _watching(repo)

    repo.git("branch", "-q", "-d", "feature")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == set()


def test_next_commit_clears_ghost_commits(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    replaced = repo.commit("Tippfeler")
    model = _watching(repo)
    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")
    model.notifyRepositoryChanged()
    assert _ghosts(model) == {replaced}

    repo.commit("Weiter")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == set()
    assert replaced not in _commit_rows(model)
    assert prop(model, "ghostCommitHashes") == []


def test_clear_ghost_commits_removes_them(repo: GitRepo) -> None:
    base, f1, f2 = _two_commit_feature_branch(repo)
    model = _watching(repo)
    repo.git("rebase", "-q", "main")
    model.notifyRepositoryChanged()
    assert _ghosts(model) == {f1, f2}

    model.clearGhostCommits()

    assert _ghosts(model) == set()
    assert f1 not in _commit_rows(model) and f2 not in _commit_rows(model)
    assert _ghost_edges(model) == set()
    # They stay gone at the next refresh.
    model.notifyRepositoryChanged()
    assert _ghosts(model) == set()


def test_working_tree_only_change_keeps_ghost_commits(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    replaced = repo.commit("Tippfeler")
    model = _watching(repo)
    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")
    model.notifyRepositoryChanged()

    repo.write("notizen.txt", "neu\n")
    model.notifyRepositoryChanged()
    repo.git("add", "notizen.txt")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == {replaced}


def test_no_ghost_commits_on_startup(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.commit("Tippfeler")
    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")  # before the Live View starts

    model = _watching(repo)

    assert _ghosts(model) == set()
    assert prop(model, "ghostCommitHashes") == []


def test_commits_beyond_the_display_limit_are_not_ghost_commits(repo: GitRepo) -> None:
    for index in range(3):
        repo.commit(f"Commit {index}")
    model = _watching(repo, max_commits=3)

    repo.commit("Commit 3")  # pushes the oldest commit out of the shown History
    model.notifyRepositoryChanged()

    assert _ghosts(model) == set()


def test_a_commit_reachable_only_from_the_stash_becomes_a_ghost_commit(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    replaced = repo.commit("Tippfeler")
    repo.write("README.md", "ungesichert\n")
    repo.git("stash", "-q")
    model = _watching(repo)

    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == {replaced}


def test_commits_left_behind_by_a_detached_head_become_ghost_commits(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("checkout", "-q", "--detach")
    model = _watching(repo)
    detached = repo.commit("Ausprobiert")
    model.notifyRepositoryChanged()

    repo.git("switch", "-q", "main")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == {detached}


def test_ghost_commits_accumulate_until_a_ref_moves(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    repo.git("checkout", "-q", "--detach")
    model = _watching(repo)
    first_try = repo.commit("Versuch 1")
    model.notifyRepositoryChanged()
    repo.git("switch", "-q", "--detach", "main")
    model.notifyRepositoryChanged()  # HEAD moved; no ref moved
    second_try = repo.commit("Versuch 2")
    model.notifyRepositoryChanged()

    repo.git("switch", "-q", "main")
    model.notifyRepositoryChanged()

    assert _ghosts(model) == {first_try, second_try}


def test_ghost_commit_checked_out_again_is_shown_normally(repo: GitRepo) -> None:
    repo.commit("Erster Commit")
    replaced = repo.commit("Tippfeler")
    model = _watching(repo)
    repo.git("commit", "-q", "--amend", "-m", "Tippfehler")
    model.notifyRepositoryChanged()

    repo.git("checkout", "-q", replaced)
    model.notifyRepositoryChanged()

    assert _ghosts(model) == set()
    assert replaced in _commit_rows(model)
    assert replaced not in prop(model, "addedCommitHashes")
