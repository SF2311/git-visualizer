"""Ticket 09: Remotes and Upstream — Remote boxes, Remote-tracking Branches as labels,
Upstream pairing by git configuration, ahead/behind; the Live View never fetches.

The Remote is a second, local bare repository; clone, push and fetch are done by the
tests (standing in for the lecturer), never by the Live View.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest
from conftest import GitRepo
from model_output import rows

from git_visualizer.live_view import LiveViewModel


@pytest.fixture
def remote(tmp_path: Path) -> GitRepo:
    """An empty bare repository serving as the Remote ``origin``."""
    path = tmp_path / "remote.git"
    path.mkdir()
    bare = GitRepo(path)
    bare.git("init", "-q", "--bare", "-b", "main")
    return bare


def _clone(remote: GitRepo, path: Path) -> GitRepo:
    GitRepo(path.parent).git("clone", "-q", str(remote.path), path.name)
    return GitRepo(path)


def _refreshed(repo: GitRepo, **kwargs: Any) -> LiveViewModel:
    model = LiveViewModel(repo.path, **kwargs)
    model.notifyRepositoryChanged()
    return model


def _branch(model: LiveViewModel, name: str) -> dict[str, Any]:
    [label] = [b for b in rows(model, "branchLabels") if b["name"] == name]
    return label


def _remote_tracking(model: LiveViewModel) -> dict[str, dict[str, Any]]:
    return {label["name"]: label for label in rows(model, "remoteTrackingLabels")}


def _ahead_behind(model: LiveViewModel, branch: str) -> tuple[int, int]:
    label = _branch(model, branch)
    return label["ahead"], label["behind"]


def _published(repo: GitRepo, remote: GitRepo) -> None:
    """``repo`` has a commit on ``main``, pushed with ``push -u`` to ``remote``."""
    repo.commit("Erster Commit")
    repo.git("remote", "add", "origin", str(remote.path))
    repo.git("push", "-q", "-u", "origin", "main")


def _commit_from_another_clone(remote: GitRepo, tmp_path: Path, message: str) -> str:
    other = _clone(remote, tmp_path / "kollegin")
    commit = other.commit(message, file="kollegin.txt")
    other.git("push", "-q")
    return commit


# --- Remotes ---------------------------------------------------------------------


def test_a_remote_appears_with_its_name_url_and_remote_tracking_branches(
    repo: GitRepo, remote: GitRepo
) -> None:
    _published(repo, remote)
    repo.git("switch", "-q", "-c", "feature")
    repo.git("push", "-q", "origin", "feature")

    [box] = rows(_refreshed(repo), "remotes")

    assert box["name"] == "origin"
    assert box["url"] == str(remote.path)
    assert box["shortUrl"].endswith("remote.git")
    assert [b["name"] for b in box["trackingBranches"]] == ["origin/feature", "origin/main"]


def test_no_remotes_without_remote_configuration(repo: GitRepo) -> None:
    repo.commit("Erster Commit")

    model = _refreshed(repo)

    assert rows(model, "remotes") == []
    assert rows(model, "remoteTrackingLabels") == []


def test_a_cloned_repository_shows_its_remote_and_remote_tracking_branches(
    remote: GitRepo, tmp_path: Path
) -> None:
    seed = _clone(remote, tmp_path / "seed")
    seed.commit("Erster Commit")
    seed.git("push", "-q", "origin", "main")

    clone = _clone(remote, tmp_path / "clone")
    model = _refreshed(clone)

    assert [box["name"] for box in rows(model, "remotes")] == ["origin"]
    labels = _remote_tracking(model)
    assert set(labels) == {"origin/main"}  # origin/HEAD is not a branch of its own
    assert labels["origin/main"]["remote"] == "origin"
    assert _branch(model, "main")["upstream"] == "origin/main"


def test_a_remote_added_and_fetched_shows_its_remote_tracking_branches(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    published = _commit_from_another_clone(remote, tmp_path, "Vom Remote")
    repo.git("remote", "add", "origin", str(remote.path))
    repo.git("fetch", "-q", "origin")

    model = _refreshed(repo)

    labels = _remote_tracking(model)
    assert labels["origin/main"]["commitHash"] == published
    assert labels["origin/main"]["column"] >= 0


# --- Last fetch -----------------------------------------------------------------------


def test_last_fetch_time_comes_from_the_latest_fetch(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    _published(repo, remote)
    assert rows(_refreshed(repo), "remotes")[0]["lastFetched"] == 0  # pushed, never fetched

    _commit_from_another_clone(remote, tmp_path, "Vom Remote")
    before = time.time()
    repo.git("fetch", "-q")

    last_fetched = rows(_refreshed(repo), "remotes")[0]["lastFetched"]
    assert before - 2 <= last_fetched <= time.time() + 1


def test_a_fetch_without_news_still_counts_as_fetched(repo: GitRepo, remote: GitRepo) -> None:
    _published(repo, remote)
    repo.git("fetch", "-q")

    assert rows(_refreshed(repo), "remotes")[0]["lastFetched"] > 0


def test_a_fresh_clone_counts_as_fetched(remote: GitRepo, tmp_path: Path) -> None:
    seed = _clone(remote, tmp_path / "seed")
    seed.commit("Erster Commit")
    seed.git("push", "-q", "origin", "main")

    clone = _clone(remote, tmp_path / "clone")

    assert rows(_refreshed(clone), "remotes")[0]["lastFetched"] > 0


@pytest.mark.parametrize(
    ("age_seconds", "text"),
    [
        (5, "zuletzt geholt gerade eben"),
        (12 * 60 + 30, "zuletzt geholt vor 12 Min."),
        (3 * 3600 + 60, "zuletzt geholt vor 3 Std."),
        (26 * 3600, "zuletzt geholt vor 1 Tag"),
        (5 * 86400, "zuletzt geholt vor 5 Tagen"),
    ],
)
def test_last_fetch_text_is_relative_and_german(repo: GitRepo, age_seconds: int, text: str) -> None:
    model = _refreshed(repo)
    now = 1_800_000_000.0

    assert model.lastFetchText(now - age_seconds, now) == text


def test_last_fetch_text_for_a_remote_never_fetched(repo: GitRepo) -> None:
    assert _refreshed(repo).lastFetchText(0, time.time()) == "noch nie geholt"


# --- Upstream and ahead/behind -----------------------------------------------------


def test_push_u_sets_the_upstream_and_pairs_the_colors(repo: GitRepo, remote: GitRepo) -> None:
    _published(repo, remote)

    model = _refreshed(repo)

    main = _branch(model, "main")
    assert main["upstream"] == "origin/main"
    assert _ahead_behind(model, "main") == (0, 0)
    origin_main = _remote_tracking(model)["origin/main"]
    assert origin_main["colorIndex"] == main["colorIndex"]
    assert origin_main["isUpstream"] is True
    [box] = rows(model, "remotes")
    assert box["trackingBranches"][0]["colorIndex"] == main["colorIndex"]


def test_a_local_commit_is_one_ahead(repo: GitRepo, remote: GitRepo) -> None:
    _published(repo, remote)
    repo.commit("Lokal")

    assert _ahead_behind(_refreshed(repo), "main") == (1, 0)


def test_a_commit_pushed_from_another_clone_is_one_behind_after_fetch(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    _published(repo, remote)
    _commit_from_another_clone(remote, tmp_path, "Von der Kollegin")
    assert _ahead_behind(_refreshed(repo), "main") == (0, 0)  # not fetched yet

    repo.git("fetch", "-q")

    assert _ahead_behind(_refreshed(repo), "main") == (0, 1)


def test_diverged_branch_is_ahead_and_behind(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    _published(repo, remote)
    _commit_from_another_clone(remote, tmp_path, "Von der Kollegin")
    repo.commit("Lokal 1")
    repo.commit("Lokal 2")
    repo.git("fetch", "-q")

    assert _ahead_behind(_refreshed(repo), "main") == (2, 1)


def test_branch_without_upstream_has_no_counter_despite_same_named_remote_tracking_branch(
    repo: GitRepo, remote: GitRepo
) -> None:
    _published(repo, remote)
    repo.git("switch", "-q", "-c", "feature")
    repo.commit("Feature", file="feature.txt")
    repo.git("push", "-q", "origin", "feature")  # no -u: no Upstream
    repo.commit("Feature lokal", file="feature.txt")

    model = _refreshed(repo)

    feature = _branch(model, "feature")
    assert feature["upstream"] == ""
    assert _ahead_behind(model, "feature") == (-1, -1)
    origin_feature = _remote_tracking(model)["origin/feature"]
    assert origin_feature["isUpstream"] is False
    assert origin_feature["colorIndex"] != feature["colorIndex"]


def test_upstream_removed_on_the_remote_side_has_no_counter(repo: GitRepo, remote: GitRepo) -> None:
    _published(repo, remote)
    repo.git("update-ref", "-d", "refs/remotes/origin/main")  # e.g. after `fetch --prune`

    model = _refreshed(repo)

    assert _branch(model, "main")["upstream"] == "origin/main"
    assert _ahead_behind(model, "main") == (-1, -1)


# --- History -------------------------------------------------------------------------


def test_fetched_but_unmerged_commits_are_shown(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    _published(repo, remote)
    fetched = _commit_from_another_clone(remote, tmp_path, "Von der Kollegin")
    repo.git("fetch", "-q")

    model = _refreshed(repo)

    commits = {c["hash"]: c for c in rows(model, "commits")}
    assert fetched in commits
    origin_main = _remote_tracking(model)["origin/main"]
    assert origin_main["commitHash"] == fetched
    assert origin_main["column"] == commits[fetched]["column"]
    assert origin_main["lane"] == commits[fetched]["lane"]
    # The fetched commit belongs with main: it takes main's color.
    assert commits[fetched]["colorIndex"] == _branch(model, "main")["colorIndex"]


def test_remote_tracking_label_is_stacked_with_the_branch_on_the_same_commit(
    repo: GitRepo, remote: GitRepo
) -> None:
    _published(repo, remote)

    model = _refreshed(repo)

    main = _branch(model, "main")
    origin_main = _remote_tracking(model)["origin/main"]
    assert (origin_main["column"], origin_main["lane"]) == (main["column"], main["lane"])
    slots = {main["stackIndex"], origin_main["stackIndex"], model.property("headStackIndex")}
    assert len(slots) == 3


# --- The Live View never fetches -------------------------------------------------------


def _state(path: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(file.relative_to(path)): (file.read_bytes(), file.stat().st_mtime_ns)
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def test_refresh_never_contacts_the_remote(
    repo: GitRepo, remote: GitRepo, tmp_path: Path
) -> None:
    _published(repo, remote)
    old_tip = repo.git("rev-parse", "HEAD").strip()
    new_tip = _commit_from_another_clone(remote, tmp_path, "Von der Kollegin")
    observed_before = _state(repo.path)
    remote_before = _state(remote.path)

    model = LiveViewModel(repo.path)
    for _ in range(3):
        model.notifyRepositoryChanged()

    assert _remote_tracking(model)["origin/main"]["commitHash"] == old_tip
    assert new_tip not in {c["hash"] for c in rows(model, "commits")}
    assert _state(repo.path) == observed_before
    assert _state(remote.path) == remote_before

    repo.git("fetch", "-q")  # the lecturer fetches
    model.notifyRepositoryChanged()

    assert _remote_tracking(model)["origin/main"]["commitHash"] == new_tip


@pytest.mark.parametrize(
    ("url", "short_url"),
    [
        ("https://example.invalid/kurs/projekt.git", "example.invalid/kurs/projekt"),
        ("https://dozent:geheim@example.invalid/kurs/projekt", "example.invalid/kurs/projekt"),
        ("git@example.invalid:kurs/projekt.git", "example.invalid:kurs/projekt"),
        ("ssh://git@example.invalid:2222/kurs/projekt.git", "example.invalid:2222/kurs/projekt"),
        ("/srv/git/vorlesungen/wintersemester/kurs/projekt.git", "…/kurs/projekt.git"),
    ],
)
def test_an_unreachable_remote_is_shown_with_a_shortened_url(
    repo: GitRepo, url: str, short_url: str
) -> None:
    repo.commit("Erster Commit")
    repo.git("remote", "add", "origin", url)

    [box] = rows(_refreshed(repo), "remotes")

    assert box["shortUrl"] == short_url
    assert box["trackingBranches"] == []
    assert box["lastFetched"] == 0
